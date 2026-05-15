import os
import shlex
import subprocess
from rich.console import Console
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path

console = Console()


def execute_command(command: str, directory_path: str) -> str:
    """Runs a terminal command strictly within the BBB Sandbox and demands Human Approval."""
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.neuroanatomy.limbic.amygdala import scan_command

    # 1. SHIFT-LEFT: Sandbox Enforcement
    is_safe_path_result, path_result = validate_execution_path(directory_path)
    if not is_safe_path_result:
        return f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>"

    # 2. SHIFT-LEFT: Semantic Intent Check
    is_safe_command, command_result = scan_command(command)
    if not is_safe_command:
        return f"<shell_output>\n<stderr>\n{command_result}\n</stderr>\n</shell_output>"

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
                return "<shell_output>\n<stderr>\nSECURITY BLOCK: Executing raw shell binaries is forbidden. Write Python scripts instead.\n</stderr>\n</shell_output>"

            if binary in ["python", "python3", "py", "uv"]:
                # Catch file execution: python script.py
                for idx, arg in enumerate(args):
                    if arg.endswith(".py") and arg != "orchestrator.py":
                        script_path = os.path.join(path_result, arg)

                        # 1. Static check (AST)
                        is_safe_ast, ast_reason = scan_python_ast(script_path)
                        if not is_safe_ast:
                            return f"<shell_output>\n<stderr>\n{ast_reason}\n</stderr>\n</shell_output>"

                        # 2. Runtime check (APOPTOSIS MEMBRANE)
                        # We rewrite the command to execute the secure membrane instead of the raw script!
                        membrane_script = wrap_with_apoptosis(script_path)
                        args[idx] = membrane_script
                        break  # Only wrap the primary target script
    except ValueError:
        pass  # shlex parsing error caught by subprocess

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
            return "<shell_output>\n<stderr>\nSECURITY BLOCK: User explicitly denied command execution.\n</stderr>\n</shell_output>"

    # 5. Execution (SECURED: shell=False + shlex)
    try:
        # Safely parse the command string into an array to prevent RCE injection
        args = shlex.split(command)
        result = subprocess.run(
            args,
            shell=False,
            cwd=path_result,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Microglia Autonomous Bug Fixing
        if result.returncode != 0:
            from System.neuroanatomy.systemic.microglia import trigger_immune_response

            trigger_immune_response(command, result.stderr, path_result)

        # XML Data Contract
        return f"<shell_output>\n<stdout>\n{result.stdout}\n</stdout>\n<stderr>\n{result.stderr}\n</stderr>\n</shell_output>"
    except subprocess.TimeoutExpired:
        return "<shell_output>\n<stderr>\nERROR: Command timed out after 60 seconds.\n</stderr>\n</shell_output>"
    except Exception as e:
        return f"<shell_output>\n<stderr>\nEXECUTION ERROR: {str(e)}\n</stderr>\n</shell_output>"


def analyze_safe_syntax(filepath: str) -> str:
    """Runs a read-only local linter against a file to check for syntax errors."""
    target_path = (ROOT_DIR / filepath).resolve()

    # SHIFT-LEFT SECURITY: Always check authorization BEFORE existence
    if not is_safe_path(target_path):
        return f"SECURITY BLOCK: Cannot lint outside allowed directories. Attempted to access {target_path}"

    if not target_path.exists():
        return f"ERROR: File '{filepath}' does not exist."

    # Only lint supported file types
    if target_path.suffix == ".py":
        try:
            # Run ruff check without modifying the file (--no-cache to avoid ghost state)
            result = subprocess.run(
                ["uv", "run", "ruff", "check", "--no-cache", str(target_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return f"✅ Linter passed for {filepath}. No syntax errors found."
            else:
                return f"❌ Linter found errors in {filepath}:\n{result.stdout}\n{result.stderr}"
        except Exception as e:
            return f"ERROR: Failed to run linter subprocess. Details: {e}"
    else:
        return f"WARNING: Syntax analysis for {target_path.suffix} files is not yet implemented. Only .py files are currently supported."


def manage_background_process(
    action: str, name: str = "", command: str = "", cwd: str = ""
) -> str:
    """
    Proprioception Motor Control: Start, stop, or list background processes (like local dev servers).
    """
    from System.neuroanatomy.autonomic.proprioception import (
        start_process,
        stop_process,
        list_processes,
    )

    if action == "list":
        return list_processes()
    elif action == "start":
        if not name or not command:
            return "Error: Both 'name' and 'command' are required to start a process."
        return start_process(name, command, cwd if cwd else None)
    elif action == "stop":
        if not name:
            return "Error: 'name' is required to stop a process."
        return stop_process(name)
    else:
        return "Error: Invalid action. Must be 'start', 'stop', or 'list'."
