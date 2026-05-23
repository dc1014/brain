# --- System/tools/execution/__init__.py ---
import os
import sys
import stat
import shlex
import socket
import asyncio
import threading
import subprocess
import signal
import shutil as shutil
from pathlib import Path

from typing import Optional, Dict, Any, Tuple

from rich.console import Console
from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult
from System.tools.sandbox import is_safe_path

# Internal Decoupled Submodule Imports with Explicit Re-exports to satisfy F401
from .validation import parse_and_validate_args as parse_and_validate_args
from .staging import stage_ast_snapshots as stage_ast_snapshots
from .routing import execute_command_async as execute_command_async

console = Console()
MAX_OUTPUT_CHUNKS = 2000
CHUNK_SIZE = 4096


def _set_system_volume_mask(read_only: bool) -> None:
    """🛡️ VOLUME MASKING: Toggles strict kernel-level file protections on the protected System/ directory."""
    try:
        import System.tools.execution

        root_dir = getattr(System.tools.execution, "ROOT_DIR", ROOT_DIR)
        system_core_dir = Path(root_dir / "System").resolve()
        if not system_core_dir.exists():
            return
        for item in system_core_dir.rglob("*"):
            try:
                rel_path_str = str(item.relative_to(system_core_dir))
            except ValueError:
                rel_path_str = str(item)
            if (
                "Temp" in rel_path_str
                or "pytest-" in rel_path_str
                or "apoptosis" in rel_path_str
            ):
                continue
            if item.is_file():
                try:
                    current_mode = os.stat(item).st_mode
                    if read_only:
                        os.chmod(
                            item,
                            current_mode
                            & ~stat.S_IWRITE
                            & ~stat.S_IWGRP
                            & ~stat.S_IWOTH,
                        )
                    else:
                        os.chmod(item, current_mode | stat.S_IWRITE)
                except Exception:
                    pass
    except Exception:
        pass


def _get_scrubbed_env() -> Dict[str, str]:
    safe_env: Dict[str, str] = {}
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


def _rollback_workspace_transaction(path_result: str) -> None:
    """⚡ TRANSACTION RECOVERY: Automatically purges modifications on execution failure."""
    try:
        target_dir = Path(path_result).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            return
        for item in list(target_dir.rglob("*")):
            try:
                if item.is_file() and (
                    ".immutable_snapshot_" in item.name
                    or ".wrapped_" in item.name
                    or "apoptosis_membrane" in item.name
                ):
                    # Enforce strict traditional os module namespace hooks for spy capture compliance
                    os.chmod(str(item), stat.S_IWRITE)
                    os.remove(str(item))
            except Exception:
                pass
    except Exception:
        pass


def _get_subprocess_kwargs() -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {}
    if sys.platform == "win32":
        # Required for clean cancellation via CTRL_BREAK_EVENT on Windows
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    # ⚡ LEGACY DEBT REMOVED: No longer relying on POSIX preexec_fn jails. We use WASM isolation instead.
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
                    output_chunks.append(
                        "\nSECURITY BLOCK: Execution halted due to excessive output"
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
        return False, await asyncio.wait_for(_stream(), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            if sys.platform == "win32":
                os.kill(process.pid, signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            process.kill()
        return True, ""


def execute_command(
    command: str, directory_path: str, route: str = "UNKNOWN"
) -> ExecutionResult:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        result = ExecutionResult(success=False, output="Thread failed")

        def run_in_thread():
            nonlocal result
            result = asyncio.run(execute_command_async(command, directory_path, route))

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        return result
    return asyncio.run(execute_command_async(command, directory_path, route))


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
            res = subprocess.run(
                ["uv", "run", "ruff", "check", "--no-cache", str(target_path)],
                capture_output=True,
                text=True,
                timeout=30,
                env=_get_scrubbed_env(),
                **_get_subprocess_kwargs(),
            )
            return (
                ExecutionResult(
                    success=True,
                    output=f"✅ Linter passed for {filepath}. No syntax errors found.",
                )
                if res.returncode == 0
                else ExecutionResult(
                    success=True,
                    output=f"❌ Linter found errors in {filepath}:\n{res.stdout}\n{res.stderr}",
                )
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False, output="Syntax linter timed out.", block_reason="Timeout"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=f"ERROR: Failed to run linter. Details: {str(e)}",
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
        manage_background_process as pm,
    )

    return pm(action=action, name="", command=command, cwd=cwd_path, port=port)


async def deploy_project_async(
    directory_path: str, provider: str = "custom", route: str = "UNKNOWN"
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
    if os.environ.get("BRAIN_EXECUTION_TIER", "0") != "1":
        return ExecutionResult(
            success=False,
            output="<shell_output>\n<stderr>\nSECURITY BLOCK: Deployments mandate Tier 1 (Hardware Sandbox) isolation. Set BRAIN_EXECUTION_TIER=1.\n</stderr>\n</shell_output>",
            block_reason="Tier 1 Mandate",
        )

    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
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
        cmd_args = (
            ["npx", "vercel", "--yes", "--prod"]
            if provider.lower() == "vercel"
            else ["npx", "netlify", "deploy", "--prod"]
            if provider.lower() == "netlify"
            else ["node", "-e", "console.log('Simulated deploy for WebProject')"]
        )
        from System.tools.sandbox import execute_in_sandbox

        return await execute_in_sandbox(
            shlex.join(cmd_args),
            normalize_path(ROOT_DIR / directory_path),
            env_secrets={"DEPLOYMENT_TOKEN": token},
            route=route,
        )
    except Exception:
        return ExecutionResult(
            success=False,
            output="DEPLOYMENT ERROR: Subprocess execution failed.",
            block_reason="Crash",
        )


def deploy_project(
    directory_path: str, provider: str = "custom", route: str = "UNKNOWN"
) -> ExecutionResult:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        result = ExecutionResult(success=False, output="Thread failed")

        def run_in_thread():
            nonlocal result
            result = asyncio.run(deploy_project_async(directory_path, provider, route))

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        return result
    return asyncio.run(deploy_project_async(directory_path, provider, route))


async def execute_native_isolated(
    command: str, workspace_path: Path, env_secrets: Dict[str, str]
) -> ExecutionResult:
    env = _get_scrubbed_env()
    for key, value in env_secrets.items():
        env[key] = value
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(workspace_path.resolve()),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        output_str = stdout.decode(errors="replace") if stdout else ""
        return ExecutionResult(
            success=proc.returncode == 0,
            output=output_str,
            block_reason=None
            if proc.returncode == 0
            else f"Native execution failed with exit code {proc.returncode}",
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            output="",
            block_reason=f"Native execution exception: {str(e)}",
        )
