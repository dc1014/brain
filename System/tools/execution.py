import os
import shlex
import subprocess
import asyncio
import threading
import signal
import socket
import sys
import importlib.util
import uuid
import stat
import shutil
from pathlib import Path
from typing import Optional, Any, Tuple, List, Set

from rich.console import Console
from System.core.paths import ROOT_DIR, normalize_path
from .sandbox import is_safe_path
from System.core.schemas import ExecutionResult

console = Console()

MAX_OUTPUT_CHUNKS = 2000
CHUNK_SIZE = 4096


def _get_scrubbed_env() -> dict[str, str]:
    safe_env: dict[str, str] = {}
    allowlist = {
        "PATH",
        "SYSTEMROOT",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "HOME",
        "USER",
        "SHELL",
        "TERM",
        "LANG",
        "TMP",
        "TEMP",
        "VIRTUAL_ENV",
        "UV_PYTHON",
        "UV_PROJECT_ENVIRONMENT",
    }
    for k, v in os.environ.items():
        if k.upper() in allowlist:
            safe_env[k] = v
    return safe_env


def _apply_unix_resource_limits() -> None:
    if sys.platform != "win32":
        try:
            os.setsid()
        except Exception:
            pass
        try:
            import resource

            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))
        except Exception:
            pass


def _get_subprocess_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["preexec_fn"] = _apply_unix_resource_limits
    return kwargs


async def _stream_and_prune_process(
    process: asyncio.subprocess.Process, timeout: float
) -> Tuple[bool, str]:
    async def _stream() -> str:
        output_chunks, chunk_count = [], 0
        if process.stdout:
            while True:
                chunk = await process.stdout.read(CHUNK_SIZE)
                if not chunk:
                    break
                decoded_chunk = chunk.decode(errors="replace")
                console.print(decoded_chunk, end="")
                output_chunks.append(decoded_chunk)
                chunk_count += 1

                if chunk_count > MAX_OUTPUT_CHUNKS:
                    console.print(
                        "\n[bold red]🚨 SYSTEM HALT: Output buffer overflow detected. Pruning rogue process.[/bold red]"
                    )
                    output_chunks.append(
                        "\n[SECURITY BLOCK: Execution halted due to excessive output (Memory Protection)]"
                    )
                    try:
                        if sys.platform == "win32":
                            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                        else:
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except Exception:
                        process.kill()
                    break
        await process.wait()
        return "".join(output_chunks)

    try:
        full_output = await asyncio.wait_for(_stream(), timeout=timeout)
        return False, full_output
    except asyncio.TimeoutError:
        try:
            if sys.platform == "win32":
                os.kill(process.pid, signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            process.kill()
        return True, ""


def _run_tier_1_microsandbox(command: str, target_dir: Path) -> ExecutionResult:
    console.print(
        f"[bold cyan]🛡️ Micro-Sandbox Requested: Attempting hardware isolation for {target_dir.name}...[/bold cyan]"
    )
    try:
        if importlib.util.find_spec("microsandbox") is None:
            console.print(
                "[bold red]🚨 SYSTEM HALT: Tier 1 execution requested, but 'microsandbox' is not installed.[/bold red]"
            )
            reason = "SECURITY BLOCK: Hardware isolation engine not found. To enable Tier 1, run `uv add microsandbox`. To use Native execution, set BRAIN_EXECUTION_TIER=0."
            return ExecutionResult(
                success=False, output=reason, block_reason="Missing Isolation Engine"
            )
        return ExecutionResult(
            success=False,
            output="Sandbox engine initialized but execution routing is WIP.",
            block_reason="WIP",
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            output=f"Sandbox failure: {str(e)}",
            block_reason="Sandbox crash",
        )


def _parse_and_validate_args(
    command: str,
) -> Tuple[Optional[List[str]], Optional[Set[str]], Optional[ExecutionResult]]:
    if sys.platform == "win32":
        if command.startswith("npm "):
            command = command.replace("npm ", "npm.cmd ", 1)
        elif command.startswith("npx "):
            command = command.replace("npx ", "npx.cmd ", 1)

    if "npm install" in command and "--no-audit" not in command:
        command += " --no-audit --no-fund"

    if sys.platform == "win32" and (
        "npm" in command.lower() or "npx" in command.lower()
    ):
        if any(char in command for char in ["&", "|", ";", "<", ">", "\n", "\r"]):
            reason = "SECURITY BLOCK: Shell chaining operators (and newlines) are strictly forbidden in npm/npx commands to prevent Windows CMD injection."
            return (
                None,
                None,
                ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                    block_reason="CMD Injection",
                ),
            )

    try:
        is_posix = sys.platform != "win32"
        raw_args = shlex.split(command, posix=is_posix)
        args = [arg.strip("\"'") for arg in raw_args] if not is_posix else raw_args
    except ValueError as e:
        reason = f"SECURITY BLOCK: Malformed command syntax ({str(e)}). Ensure quotes are properly closed."
        return (
            None,
            None,
            ExecutionResult(
                success=False,
                output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                block_reason="Malformed Syntax",
            ),
        )

    if not args:
        return (
            None,
            None,
            ExecutionResult(
                success=False,
                output="<shell_output>\n<stderr>\nEmpty command.\n</stderr>\n</shell_output>",
                block_reason="Empty",
            ),
        )

    binary = Path(args[0]).stem.lower()
    effective_binaries = {binary}

    allowed_native_binaries = {
        "python",
        "python3",
        "py",
        "uv",
        "npm",
        "npx",
        "echo",
        "dir",
        "ls",
        "cat",
        "type",
        "pytest",
    }
    if binary not in allowed_native_binaries:
        reason = f"SECURITY BLOCK: Execution of '{binary}' natively is strictly forbidden to prevent non-AST sandbox escapes."
        return (
            None,
            None,
            ExecutionResult(
                success=False,
                output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                block_reason=reason,
            ),
        )

    resolved_bin = shutil.which(args[0])
    if resolved_bin:
        resolved_path = Path(resolved_bin).resolve()
        if resolved_path.is_relative_to(ROOT_DIR.resolve()):
            reason = f"SECURITY BLOCK: Local binary hijacking detected. '{args[0]}' resolved to a workspace path: {resolved_path}"
            return (
                None,
                None,
                ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                    block_reason="Binary Hijacking",
                ),
            )
        args[0] = str(resolved_path)
    else:
        if binary in ["python", "python3", "py", "uv", "npm", "npx", "pytest"]:
            reason = f"SECURITY BLOCK: System binary '{args[0]}' could not be found in host PATH."
            return (
                None,
                None,
                ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                    block_reason="Missing System Binary",
                ),
            )

    if binary in ["uv", "npx", "npm", "npm.cmd", "npx.cmd"]:
        primary_nested_executable, primary_raw_target = None, None
        all_nested_tokens = []
        skip_next = False
        value_consuming_flags = {
            "-p",
            "--package",
            "--python",
            "--with",
            "--directory",
            "-c",
        }

        for idx, arg in enumerate(args[1:], start=1):
            if skip_next:
                skip_next = False
                continue
            if arg.lower() in value_consuming_flags:
                if idx + 1 < len(args):
                    all_nested_tokens.append(Path(args[idx + 1]).stem.lower())
                skip_next = True
                continue
            if "=" in arg and arg.startswith("-"):
                parts = arg.split("=", 1)
                if len(parts) == 2:
                    all_nested_tokens.append(Path(parts[1]).stem.lower())
                continue
            if not arg.startswith("-"):
                if arg.lower() in ["run", "exec"]:
                    continue
                token = Path(arg).stem.lower()
                all_nested_tokens.append(token)
                if primary_nested_executable is None:
                    primary_nested_executable, primary_raw_target = token, arg

        if primary_nested_executable and primary_raw_target:
            if (
                "." not in primary_raw_target
                and "/" not in primary_raw_target
                and "\\" not in primary_raw_target
            ):
                safe_nested = {
                    "python",
                    "python3",
                    "py",
                    "pytest",
                    "ruff",
                    "pip",
                    "tsc",
                    "vite",
                    "next",
                    "react-scripts",
                    "vercel",
                    "netlify",
                    "build",
                    "dev",
                    "start",
                    "test",
                    "lint",
                }
                if primary_nested_executable not in safe_nested:
                    reason = f"SECURITY BLOCK: Smuggled nested binary '{primary_nested_executable}' is not in the strict allowlist."
                    return (
                        None,
                        None,
                        ExecutionResult(
                            success=False,
                            output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                            block_reason="Nested Sandbox Escape",
                        ),
                    )
                effective_binaries.add(primary_nested_executable)

        forbidden_nested_binaries = {
            "node",
            "bash",
            "sh",
            "zsh",
            "cmd",
            "powershell",
            "pwsh",
        }
        for token in all_nested_tokens:
            if token in forbidden_nested_binaries:
                reason = (
                    f"SECURITY BLOCK: Smuggled forbidden binary '{token}' detected."
                )
                return (
                    None,
                    None,
                    ExecutionResult(
                        success=False,
                        output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                        block_reason="Nested Sandbox Escape",
                    ),
                )

    forbidden_nested_binaries = {
        "node",
        "bash",
        "sh",
        "zsh",
        "cmd",
        "powershell",
        "pwsh",
    }
    is_python_execution = any(
        b in ["python", "python3", "py"] for b in effective_binaries
    )

    for arg in args:
        if Path(arg).stem.lower() in forbidden_nested_binaries:
            reason = f"SECURITY BLOCK: Smuggled forbidden binary '{arg}' detected."
            return (
                None,
                None,
                ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                    block_reason="Nested Sandbox Escape",
                ),
            )

        if is_python_execution:
            if arg.startswith("-") and not arg.startswith("--"):
                if any(char in arg for char in ["c", "m", "i"]):
                    reason = "SECURITY BLOCK: Merged or inline Python flags (-c, -m, -i) are forbidden to prevent AST evasion."
                    return (
                        None,
                        None,
                        ExecutionResult(
                            success=False,
                            output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                            block_reason="AST Bypass",
                        ),
                    )
            elif arg in ["--command", "--module", "--interactive"]:
                reason = "SECURITY BLOCK: Inline/Module Python execution is forbidden."
                return (
                    None,
                    None,
                    ExecutionResult(
                        success=False,
                        output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                        block_reason="AST Bypass",
                    ),
                )

        if arg.endswith((".pyc", ".pyo", ".pyd", ".pyw")):
            reason = "SECURITY BLOCK: Executing compiled Python bytecode (.pyc) is strictly forbidden."
            return (
                None,
                None,
                ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                    block_reason="Bytecode Bypass",
                ),
            )

    return args, effective_binaries, None


def _stage_ast_snapshots(
    args: List[str], effective_binaries: Set[str], path_result: str
) -> Tuple[Optional[List[str]], List[str], Optional[ExecutionResult]]:
    from System.neuroanatomy.systemic.blood_brain_barrier import (
        scan_python_ast,
        wrap_with_apoptosis,
    )

    # ⚡ THE FIX: Explicitly annotate the empty list for Mypy
    created_snapshots: List[str] = []

    is_pytest_run = "pytest" in effective_binaries
    is_python_execution = any(
        b in ["python", "python3", "py"] for b in effective_binaries
    )

    if is_pytest_run:
        # ⚡ THE FIX: Ignore args[0] so absolute system paths don't trigger the traversal block
        for arg in args[1:]:
            if (
                ".." in arg
                or arg.startswith("/")
                or arg.startswith("\\")
                or ":\\" in arg
                or ":/" in arg
            ):
                reason = "SECURITY BLOCK: Path traversal and absolute paths are strictly forbidden in pytest arguments."
                return (
                    None,
                    created_snapshots,
                    ExecutionResult(
                        success=False,
                        output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                        block_reason="Pytest Traversal",
                    ),
                )

        for root, _, files in os.walk(path_result):
            for file in files:
                if file.endswith(".py"):
                    script_path = os.path.join(root, file)
                    is_safe_ast, ast_reason = scan_python_ast(script_path)
                    if not is_safe_ast:
                        return (
                            None,
                            created_snapshots,
                            ExecutionResult(
                                success=False,
                                output=f"<shell_output>\n<stderr>\n{ast_reason} in {script_path}\n</stderr>\n</shell_output>",
                                block_reason=ast_reason,
                            ),
                        )

    elif is_python_execution:
        primary_script_wrapped = False
        skip_next = False
        value_consuming_flags = {"-w", "-x"}
        if "uv" in effective_binaries:
            value_consuming_flags.update(
                {"--python", "--with", "-p", "--directory", "-c"}
            )

        for idx, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue
            if arg.lower() in value_consuming_flags:
                if idx + 1 < len(args):
                    skip_next = True
                continue

            if not arg.startswith("-") and Path(arg).stem.lower() not in [
                "python",
                "python3",
                "py",
                "uv",
                "run",
                "pytest",
                "orchestrator",
            ]:
                script_path = os.path.join(path_result, arg)
                if os.path.exists(script_path):
                    target_to_scan = script_path
                    if os.path.isdir(script_path):
                        main_path = os.path.join(script_path, "__main__.py")
                        if os.path.exists(main_path):
                            target_to_scan = main_path
                        else:
                            continue

                    is_primary = not primary_script_wrapped
                    if is_primary or target_to_scan.endswith(".py"):
                        try:
                            snapshot_filename = (
                                f".immutable_snapshot_{uuid.uuid4().hex}.py"
                            )
                            snapshot_path = os.path.join(path_result, snapshot_filename)
                            with open(target_to_scan, "rb") as src:
                                file_payload = src.read()
                            with open(snapshot_path, "wb") as dst:
                                dst.write(file_payload)
                            os.chmod(snapshot_path, stat.S_IREAD)
                            created_snapshots.append(snapshot_path)
                        except Exception as e:
                            reason = f"SECURITY BLOCK: Atomic snapshot generation failed ({str(e)})."
                            return (
                                None,
                                created_snapshots,
                                ExecutionResult(
                                    success=False,
                                    output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                                    block_reason="Snapshot Error",
                                ),
                            )

                        is_safe_ast, ast_reason = scan_python_ast(snapshot_path)
                        if not is_safe_ast:
                            return (
                                None,
                                created_snapshots,
                                ExecutionResult(
                                    success=False,
                                    output=f"<shell_output>\n<stderr>\n{ast_reason}\n</stderr>\n</shell_output>",
                                    block_reason=ast_reason,
                                ),
                            )

                        if is_primary:
                            membrane_script = wrap_with_apoptosis(snapshot_path)
                            try:
                                if os.path.exists(membrane_script):
                                    os.chmod(membrane_script, stat.S_IREAD)
                                    created_snapshots.append(membrane_script)
                            except Exception:
                                pass
                            args[idx] = membrane_script
                            primary_script_wrapped = True
                        else:
                            args[idx] = snapshot_path

    return args, created_snapshots, None


async def execute_command_async(command: str, directory_path: str) -> ExecutionResult:
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.neuroanatomy.limbic.amygdala import scan_command

    is_safe_path_result, path_result = validate_execution_path(directory_path)
    if not is_safe_path_result:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>",
            block_reason=path_result,
        )

    is_safe_command, command_result = scan_command(command)
    if not is_safe_command:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{command_result}\n</stderr>\n</shell_output>",
            block_reason=command_result,
        )

    parsed_args, effective_binaries, parse_err = _parse_and_validate_args(command)
    if parse_err:
        return parse_err
    if parsed_args is None or effective_binaries is None:
        return ExecutionResult(
            success=False,
            output="<shell_output>\n<stderr>\nInternal parser error.\n</stderr>\n</shell_output>",
            block_reason="Parse Error",
        )

    args, created_snapshots, stage_err = _stage_ast_snapshots(
        parsed_args, effective_binaries, path_result
    )

    try:
        if stage_err:
            return stage_err
        if args is None:
            return ExecutionResult(
                success=False,
                output="<shell_output>\n<stderr>\nInternal staging error.\n</stderr>\n</shell_output>",
                block_reason="Staging Error",
            )

        from System.neuroanatomy.autonomic.vestibular import create_snapshot

        create_snapshot(directory_path)

        if os.environ.get("BRAIN_OS_HEADLESS") != "1":
            display_cmd = shlex.join(args)
            console.print(
                f"\n[bold yellow]⚠️ Agent wants to execute command in {path_result}:[/bold yellow]"
            )
            console.print(f"[cyan]{display_cmd}[/cyan]")
            try:
                auth = await asyncio.to_thread(input, "Allow execution? [y/N]: ")
                auth = auth.strip().lower()
            except (EOFError, KeyboardInterrupt):
                auth = "n"
            if auth not in ["y", "yes"]:
                return ExecutionResult(
                    success=False,
                    output="<shell_output>\n<stderr>\nSECURITY BLOCK: User explicitly denied command execution.\n</stderr>\n</shell_output>",
                    block_reason="Denied",
                )

        execution_tier = os.environ.get("BRAIN_EXECUTION_TIER", "0")
        if execution_tier == "1":
            target_dir = normalize_path(ROOT_DIR / directory_path)
            return _run_tier_1_microsandbox(shlex.join(args), target_dir)

        console.print(f"\n[bold cyan]▶ Executing:[/bold cyan] {shlex.join(args)}")

        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=path_result,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=_get_scrubbed_env(),
            **_get_subprocess_kwargs(),
        )

        timed_out, full_output = await _stream_and_prune_process(process, timeout=180.0)

        if timed_out:
            return ExecutionResult(
                success=False,
                output="<shell_output>\n<stderr>\nERROR: Command timed out. Process tree violently pruned.\n</stderr>\n</shell_output>",
                block_reason="Timeout",
            )

        if process.returncode != 0:
            from System.neuroanatomy.systemic.microglia import (
                trigger_immune_response_async,
            )

            console.print(
                "\n[bold yellow]⚠️ Execution failed. Triggering Async Microglia immune response...[/bold yellow]"
            )
            healed, heal_msg = await trigger_immune_response_async(
                command, full_output, path_result
            )
            if healed:
                return ExecutionResult(
                    success=True,
                    output=f"<shell_output>\n<stdout>\n{heal_msg}\n</stdout>\n</shell_output>",
                )
            else:
                return ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{full_output}\n\nMicroglia Antibody Failed:\n{heal_msg}\n</stderr>\n</shell_output>",
                    block_reason=f"Failed with exit code {process.returncode}",
                )

        return ExecutionResult(
            success=True,
            output=f"<shell_output>\n<stdout>\n{full_output}\n</stdout>\n</shell_output>",
        )

    except Exception as e:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\nEXECUTION ERROR: {str(e)}\n</stderr>\n</shell_output>",
            block_reason="Crash",
        )

    finally:
        for snapshot in created_snapshots:
            try:
                if os.path.exists(snapshot):
                    os.chmod(snapshot, stat.S_IWRITE)
                    os.remove(snapshot)
            except Exception:
                pass


def execute_command(command: str, directory_path: str) -> ExecutionResult:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        result: ExecutionResult = ExecutionResult(
            success=False, output="Thread failed", block_reason="Thread failed"
        )

        def run_in_thread() -> None:
            nonlocal result
            result = asyncio.run(execute_command_async(command, directory_path))

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        return result
    else:
        return asyncio.run(execute_command_async(command, directory_path))


def analyze_safe_syntax(filepath: str) -> ExecutionResult:
    target_path = (ROOT_DIR / filepath).resolve()
    if not is_safe_path(target_path):
        return ExecutionResult(
            success=False,
            output="SECURITY BLOCK: Cannot lint outside allowed directories.",
            block_reason="Path Traversal",
        )
    if not target_path.exists():
        return ExecutionResult(
            success=False,
            output=f"ERROR: File '{filepath}' does not exist.",
            block_reason="File Not Found",
        )

    if target_path.suffix == ".py":
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "check", "--no-cache", str(target_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                env=_get_scrubbed_env(),
                **_get_subprocess_kwargs(),
            )
            if result.returncode == 0:
                return ExecutionResult(
                    success=True,
                    output=f"✅ Linter passed for {filepath}. No syntax errors found.",
                )
            else:
                return ExecutionResult(
                    success=True,
                    output=f"❌ Linter found errors in {filepath}:\n{result.stdout}\n{result.stderr}",
                )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="ERROR: Syntax linter timed out.",
                block_reason="Timeout",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=f"ERROR: Failed to run linter. Details: {str(e).replace(str(target_path.parent), '[SCRUBBED_PATH]')}",
                block_reason="Crash",
            )
    return ExecutionResult(
        success=True,
        output=f"WARNING: Syntax analysis for {target_path.suffix} is not yet implemented.",
    )


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def manage_background_process(
    action: str,
    command: str = "",
    port: Optional[int] = None,
    cwd_path: str = "Studio/Brain-Website",
) -> str:
    from System.neuroanatomy.autonomic.proprioception import (
        manage_background_process as proprioceptive_manage,
    )

    return proprioceptive_manage(
        action=action, name="", command=command, cwd=cwd_path, port=port
    )


async def deploy_project_async(
    directory_path: str, provider: str = "custom"
) -> ExecutionResult:
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.neuroanatomy.systemic.immune_system import vault

    is_safe_path_result, path_result = validate_execution_path(directory_path)
    if not is_safe_path_result:
        return ExecutionResult(
            success=False,
            output="SECURITY BLOCK: Cannot deploy from outside sandbox.",
            block_reason="Path Traversal",
        )

    token = vault.get_secret("DEPLOYMENT_TOKEN")
    if not token:
        return ExecutionResult(
            success=False,
            output="SECURITY BLOCK: DEPLOYMENT_TOKEN missing.",
            block_reason="No Token",
        )

    execution_tier = os.environ.get("BRAIN_EXECUTION_TIER", "0")
    if execution_tier != "1":
        return ExecutionResult(
            success=False,
            output="<shell_output>\n<stderr>\nSECURITY BLOCK: Deployments mandate Tier 1 (Hardware Sandbox) isolation. Set BRAIN_EXECUTION_TIER=1.\n</stderr>\n</shell_output>",
            block_reason="Tier 1 Mandate",
        )

    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
        console.print(
            f"\n[bold yellow]⚠️ Agent wants to DEPLOY project {path_result} via {provider.upper()} in Tier 1:[/bold yellow]"
        )
        try:
            auth = await asyncio.to_thread(input, "Allow deployment? [y/N]: ")
        except (EOFError, KeyboardInterrupt):
            auth = "n"
        if auth.strip().lower() not in ["y", "yes"]:
            return ExecutionResult(
                success=False,
                output="SECURITY BLOCK: User explicitly denied deployment.",
                block_reason="Denied",
            )

    try:
        deploy_env = _get_scrubbed_env()
        deploy_env["DEPLOYMENT_TOKEN"] = token
        console.print(
            f"\n[bold cyan]▶ Initiating {provider.upper()} deployment sequence (Tier 1 Routed)...[/bold cyan]"
        )

        if provider.lower() == "custom":
            command_args = [
                sys.executable,
                "-c",
                "import sys; print('Simulated deploy for ' + sys.argv[1])",
                path_result,
            ]
        elif provider.lower() == "vercel":
            command_args = ["npx", "vercel", "--yes", "--prod"]
        elif provider.lower() == "netlify":
            command_args = ["npx", "netlify", "deploy", "--prod"]
        else:
            return ExecutionResult(
                success=False,
                output=f"ERROR: Provider '{provider}' not supported.",
                block_reason="Unsupported",
            )

        return _run_tier_1_microsandbox(
            shlex.join(command_args), normalize_path(ROOT_DIR / directory_path)
        )
    except Exception:
        return ExecutionResult(
            success=False,
            output="DEPLOYMENT ERROR: Subprocess execution failed.",
            block_reason="Crash",
        )


def deploy_project(directory_path: str, provider: str = "custom") -> ExecutionResult:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        result: ExecutionResult = ExecutionResult(
            success=False, output="Thread failed", block_reason="Thread failed"
        )

        def run_in_thread() -> None:
            nonlocal result
            result = asyncio.run(deploy_project_async(directory_path, provider))

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        return result
    else:
        return asyncio.run(deploy_project_async(directory_path, provider))
