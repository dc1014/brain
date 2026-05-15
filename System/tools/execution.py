import os
import shlex
import subprocess
from rich.console import Console
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path
from System.core.schemas import ExecutionResult
import socket
import time
import sys
from typing import Optional, Dict

# The Motor Cortex's active memory of running background servers
ACTIVE_PROCESSES: Dict[str, subprocess.Popen] = {}


console = Console()


def execute_command(command: str, directory_path: str) -> ExecutionResult:
    """Runs a terminal command strictly within the BBB Sandbox and demands Human Approval."""
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.neuroanatomy.limbic.amygdala import scan_command

    # 1. SHIFT-LEFT: Sandbox Enforcement
    is_safe_path_result, path_result = validate_execution_path(directory_path)
    if not is_safe_path_result:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>",
            block_reason=path_result,
        )

    # 2. SHIFT-LEFT: Semantic Intent Check
    is_safe_command, command_result = scan_command(command)
    if not is_safe_command:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{command_result}\n</stderr>\n</shell_output>",
            block_reason=command_result,
        )

    # 3. SHIFT-LEFT: AST MEMBRANE & BINARY WHITELIST (Payload inspection)
    try:
        from System.neuroanatomy.systemic.blood_brain_barrier import (
            scan_python_ast,
            wrap_with_apoptosis,
        )

        args = shlex.split(command)
        if args:
            binary = args[0].lower()
            if binary in ["bash", "sh", "zsh", "powershell", "pwsh", "cmd"]:
                reason = "SECURITY BLOCK: Executing raw shell binaries is forbidden. Write Python scripts instead."
                return ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                    block_reason=reason,
                )

            if binary in ["python", "python3", "py", "uv"]:
                for idx, arg in enumerate(args):
                    if arg.endswith(".py") and arg != "orchestrator.py":
                        script_path = os.path.join(path_result, arg)
                        is_safe_ast, ast_reason = scan_python_ast(script_path)
                        if not is_safe_ast:
                            return ExecutionResult(
                                success=False,
                                output=f"<shell_output>\n<stderr>\n{ast_reason}\n</stderr>\n</shell_output>",
                                block_reason=ast_reason,
                            )
                        membrane_script = wrap_with_apoptosis(script_path)
                        args[idx] = membrane_script
                        break
    except ValueError:
        pass

    # 4. HITL Check
    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
        console.print(
            f"\n[bold yellow]⚠️ Agent wants to execute command in {path_result}:[/bold yellow]"
        )
        console.print(f"[cyan]{command}[/cyan]")
        try:
            auth = input("Allow execution? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            auth = "n"

        if auth not in ["y", "yes"]:
            reason = "SECURITY BLOCK: User explicitly denied command execution."
            return ExecutionResult(
                success=False,
                output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
                block_reason=reason,
            )

    # 5. Execution (SECURED: shell=False + shlex + STREAMING)
    try:
        args = shlex.split(command)

        console.print(f"\n[bold cyan]▶ Executing:[/bold cyan] {command}")

        process = subprocess.Popen(
            args,
            shell=False,
            cwd=path_result,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout for continuous streaming
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        output_lines = []
        # 🎯 MYPY FIX: Ensure stdout exists before iterating to satisfy the type checker
        if process.stdout:
            for line in process.stdout:
                # Stream directly to the terminal with a subtle visual prefix
                console.print(f"[dim]│ {line}[/dim]", end="")
                output_lines.append(line)

        # Wait for the process to finish with our 60-second timeout
        process.wait(timeout=60)
        full_output = "".join(output_lines)

        # Microglia Autonomous Bug Fixing
        if process.returncode != 0:
            from System.neuroanatomy.systemic.microglia import trigger_immune_response

            trigger_immune_response(command, full_output, path_result)
            return ExecutionResult(
                success=False,
                output=f"<shell_output>\n<stderr>\n{full_output}\n</stderr>\n</shell_output>",
                block_reason=f"Command failed with exit code {process.returncode}",
            )

        # XML Data Contract
        return ExecutionResult(
            success=True,
            output=f"<shell_output>\n<stdout>\n{full_output}\n</stdout>\n</shell_output>",
        )

    except subprocess.TimeoutExpired:
        process.kill()  # Safety First: Kill the zombie process
        reason = "ERROR: Command timed out after 60 seconds."
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
            block_reason=reason,
        )
    except Exception as e:
        if "process" in locals():
            process.kill()
        reason = f"EXECUTION ERROR: {str(e)}"
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{reason}\n</stderr>\n</shell_output>",
            block_reason=reason,
        )


def analyze_safe_syntax(filepath: str) -> ExecutionResult:
    """Runs a read-only local linter against a file to check for syntax errors."""
    target_path = (ROOT_DIR / filepath).resolve()

    if not is_safe_path(target_path):
        reason = f"SECURITY BLOCK: Cannot lint outside allowed directories. Attempted to access {target_path}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    if not target_path.exists():
        reason = f"ERROR: File '{filepath}' does not exist."
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    if target_path.suffix == ".py":
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "check", "--no-cache", str(target_path)],
                capture_output=True,
                text=True,
                check=False,
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
        except Exception as e:
            reason = f"ERROR: Failed to run linter subprocess. Details: {e}"
            return ExecutionResult(success=False, output=reason, block_reason=reason)
    else:
        return ExecutionResult(
            success=True,
            output=f"WARNING: Syntax analysis for {target_path.suffix} files is not yet implemented. Only .py files are currently supported.",
        )


def is_port_in_use(port: int) -> bool:
    """Proprioceptive sensory check: verifies if a port is actually transmitting."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def manage_background_process(
    action: str,
    command: str = "",
    port: Optional[int] = None,
    cwd_path: str = "Studio/Brain-Website",
) -> str:
    """
    MOTOR CORTEX: Manages non-blocking background servers (like Vite/React).
    Includes health checks to ensure the server actually bound to the port.
    """
    global ACTIVE_PROCESSES

    if action == "list":
        if not ACTIVE_PROCESSES:
            return "No active background processes."
        return "Active processes:\n" + "\n".join(
            [f"PID {p.pid}: {cmd}" for cmd, p in ACTIVE_PROCESSES.items()]
        )

    if action == "stop":
        stopped = 0
        for cmd, p in list(ACTIVE_PROCESSES.items()):
            p.terminate()
            del ACTIVE_PROCESSES[cmd]
            stopped += 1
        return f"Stopped {stopped} active processes."

    if action == "start":
        if not command:
            return "Error: Command required to start a process."

        # ⚡ SHIFT-LEFT: Cure the Windows Subprocess Bug
        if sys.platform == "win32":
            if command.startswith("npm "):
                command = command.replace("npm ", "npm.cmd ", 1)
            elif command.startswith("npx "):
                command = command.replace("npx ", "npx.cmd ", 1)

        try:
            target_dir = (ROOT_DIR / cwd_path).resolve()
            target_dir.mkdir(parents=True, exist_ok=True)

            # Start detached process so the LLM doesn't hang forever
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(target_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            ACTIVE_PROCESSES[command] = process

            # 🧠 PROPRIOCEPTION: The Health Check
            if port:
                for _ in range(15):  # Poll for 15 seconds
                    if is_port_in_use(port):
                        return f"Success: Background process started. Health check passed: Port {port} is active."
                    time.sleep(1)

                # If it failed to bind, kill it and report the crash
                process.terminate()
                del ACTIVE_PROCESSES[command]
                return f"Error: Process started but failed to bind to port {port} within 15 seconds. The server crashed (likely due to missing npm packages)."

            return f"Success: Background process started (PID {process.pid}). No port health check requested."

        except Exception as e:
            return f"Error starting background process: {str(e)}"

    return "Error: Invalid action. Use 'start', 'stop', or 'list'."


def deploy_project(directory_path: str, provider: str = "custom") -> ExecutionResult:
    """Deploys a project safely to the internet without leaking credentials."""
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.neuroanatomy.systemic.immune_system import vault

    # 1. SHIFT-LEFT: Sandbox Enforcement
    is_safe_path_result, path_result = validate_execution_path(directory_path)
    if not is_safe_path_result:
        reason = (
            f"SECURITY BLOCK: Cannot deploy from outside the sandbox. {path_result}"
        )
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    # Fetch generic deployment token
    token = vault.get_secret("DEPLOYMENT_TOKEN")
    if not token:
        reason = "SECURITY BLOCK: DEPLOYMENT_TOKEN is missing from the SecretVault."
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    # 2. HITL Check (Never deploy without human consent unless Headless)
    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
        console.print(
            f"\n[bold yellow]⚠️ Agent wants to DEPLOY project {path_result} via {provider.upper()}:[/bold yellow]"
        )
        try:
            auth = input("Allow deployment? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            auth = "n"

        if auth not in ["y", "yes"]:
            reason = "SECURITY BLOCK: User explicitly denied deployment."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

    # 3. Secure Execution Abstraction
    try:
        # Inject the token safely into the subprocess memory
        deploy_env = os.environ.copy()
        deploy_env["DEPLOYMENT_TOKEN"] = token

        console.print(
            f"\n[bold cyan]▶ Initiating {provider.upper()} deployment sequence...[/bold cyan]"
        )

        # Routing Logic for Future Providers
        if provider.lower() == "custom":
            # Cross-platform simulation command
            cmd_binary = "cmd" if os.name == "nt" else "echo"
            cmd_args = (
                ["/c", "echo", f"Simulated deployment complete for {path_result}"]
                if os.name == "nt"
                else [f"Simulated deployment complete for {path_result}"]
            )
            command = [cmd_binary] + cmd_args
        elif provider.lower() == "vercel":
            command = ["npx", "vercel", "--yes", "--prod"]
        elif provider.lower() == "netlify":
            command = ["npx", "netlify", "deploy", "--prod"]
        else:
            reason = f"ERROR: Deployment provider '{provider}' is not supported yet."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        process = subprocess.Popen(
            command,
            shell=False,
            cwd=path_result,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=deploy_env,
        )

        output_lines = []
        if process.stdout:
            for line in process.stdout:
                console.print(f"[dim]│ {line}[/dim]", end="")
                output_lines.append(line)

        process.wait(timeout=120)
        full_output = "".join(output_lines)

        if process.returncode != 0:
            return ExecutionResult(
                success=False,
                output=f"<deployment_error>\n{full_output}\n</deployment_error>",
                block_reason=f"Deployment failed with exit code {process.returncode}",
            )

        return ExecutionResult(
            success=True,
            output=f"<deployment_success>\n{full_output}\n</deployment_success>",
        )

    except subprocess.TimeoutExpired:
        process.kill()
        reason = "ERROR: Deployment timed out after 120 seconds."
        return ExecutionResult(success=False, output=reason, block_reason=reason)
    except Exception as e:
        reason = f"DEPLOYMENT ERROR: {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)
