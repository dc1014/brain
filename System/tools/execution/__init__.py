# --- System/tools/execution/__init__.py ---
import os
import socket
import asyncio
import threading
import subprocess
import shlex
from pathlib import Path

from typing import Optional, Dict

from rich.console import Console
from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult
from System.tools.sandbox import is_safe_path
from System.ui.telemetry import render_command_cockpit

from .validation import parse_and_validate_args as parse_and_validate_args
from .staging import stage_ast_snapshots as stage_ast_snapshots
from .routing import execute_command_async as execute_command_async
from .execution_utils import get_scrubbed_env, get_subprocess_kwargs

console = Console()


async def _execute_with_auth_async(
    command: list[str] | str, directory_path: str, route: str
) -> ExecutionResult:
    """Internal wrapper that handles UI, Auth, and Timeouts before invoking pure execution."""
    command_str = command if isinstance(command, str) else shlex.join(command)
    execution_tier = os.environ.get("BRAIN_EXECUTION_TIER", "0")

    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
        parsed_args, effective_binaries, parse_err = parse_and_validate_args(command)
        if parse_err is not None:
            return parse_err

        from System.neuroanatomy.systemic.blood_brain_barrier import (
            validate_execution_path,
        )

        is_safe_path_res, path_result = validate_execution_path(directory_path)
        if not is_safe_path_res:
            return ExecutionResult(
                success=False,
                output=f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>",
                block_reason=path_result,
            )

        panel = render_command_cockpit(
            command_str,
            path_result,
            effective_binaries or set(),
            [],
            execution_tier,
            ROOT_DIR,
        )
        console.print("\n")
        console.print(panel)

        try:
            auth = await asyncio.to_thread(
                input, "↳ Synaptic Authorization Handle [y/N]: "
            )
            auth = auth.strip().lower()
        except (EOFError, KeyboardInterrupt):
            auth = "n"

        if auth not in ["y", "yes"]:
            console.print(
                "\n[bold red]❌ TRANSMISSION ABORTED: Security boundary held.[/bold red]\n"
            )
            return ExecutionResult(
                success=False,
                output="<shell_output>\n<stderr>\nSECURITY BLOCK: User denied execution.\n</stderr>\n</shell_output>",
                block_reason="Denied",
            )
        else:
            console.print(
                "\n[bold green]⚡ TRANSMISSION AUTHORIZED: Firing synaptic process tree...[/bold green]\n"
            )

    # Timeouts belong to the orchestrator layer, not the routing layer
    timeout = 300.0 if "pytest" in command_str else 60.0
    return await execute_command_async(command, directory_path, route, timeout=timeout)


def execute_command(
    command: list[str] | str, directory_path: str, route: str = "UNKNOWN"
) -> ExecutionResult:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        result = ExecutionResult(success=False, output="Thread failed")

        def run_in_thread():
            nonlocal result
            result = asyncio.run(
                _execute_with_auth_async(command, directory_path, route)
            )

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        return result
    return asyncio.run(_execute_with_auth_async(command, directory_path, route))


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
                env=get_scrubbed_env(),
                **get_subprocess_kwargs(),
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
            cmd_args,
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
    command: list[str], workspace_path: Path, env_secrets: Dict[str, str]
) -> ExecutionResult:
    # Accept strictly parsed array lists to prevent shell injection payloads
    env = get_scrubbed_env()
    for key, value in env_secrets.items():
        env[key] = value
    try:
        # 🛡️ THE FIX: Use create_subprocess_exec to bypass OS shell evaluation entirely
        proc = await asyncio.create_subprocess_exec(
            *command,
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
