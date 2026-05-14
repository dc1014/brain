from System.core.paths import ROOT_DIR
import os
import re
import ast
import tempfile
from pathlib import Path
from rich.console import Console

console = Console()


def inspect_toxins(command: str) -> tuple[bool, str]:
    """
    The Blood-Brain Barrier.
    Prevents the autonomous installation of external packages during headless/dream states.
    """
    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
        return True, ""

    toxin_patterns = [
        r"\bnpm\s+(i|install|add)\b",
        r"\byarn\s+(add)\b",
        r"\bpnpm\s+(add|install)\b",
        r"\bpip\s+install\b",
        r"\buv\s+(add|pip\s+install)\b",
        r"\bbrew\s+install\b",
        r"\bapt(-get)?\s+install\b",
        r"\bcurl\b.*\|.*\b(bash|sh)\b",
        r"\bwget\b.*\|.*\b(bash|sh)\b",
    ]

    for pattern in toxin_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            console.print(
                "\n[bold red]🛑 Blood-Brain Barrier Triggered: Blocked toxic network command during REM sleep.[/bold red]"
            )
            console.print(f"[dim]Command intercepted: {command}[/dim]")
            return (
                False,
                "SECURITY BLOCK (Blood-Brain Barrier): Autonomous package installation is strictly forbidden during REM sleep to prevent supply-chain attacks. Dream with the packages you already have.",
            )

    return True, ""


def validate_execution_path(target_path: str) -> tuple[bool, str]:
    """Ensures execution directories are strictly within approved sandboxes."""
    try:
        requested_path = Path(target_path).resolve()

        # FIX: Use strict relative pathing to physically prevent traversal
        try:
            requested_path.relative_to(ROOT_DIR)
        except ValueError:
            return (
                False,
                "PATH TRAVERSAL BLOCKED: Attempted to execute outside the OS Root.",
            )

        safe_zones = ["Studio", "Personal", "Professional", "Media"]
        is_in_safe_zone = any(zone in requested_path.parts for zone in safe_zones)

        if not is_in_safe_zone:
            return (
                False,
                f"SANDBOX BLOCKED: Execution is strictly limited to {safe_zones}.",
            )

        return True, str(requested_path)
    except Exception as e:
        return False, f"PATH VALIDATION ERROR: {str(e)}"


# --- NEW: THE AST MEMBRANE ---
class ToxinDetector(ast.NodeVisitor):
    def __init__(self):
        self.is_toxic = False
        self.threat_reason = ""
        # The lethal imports an autonomous agent should NEVER need for basic logic
        self.forbidden_modules = {"os", "subprocess", "sys", "pty", "shutil", "socket"}

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split(".")[0] in self.forbidden_modules:
                self.is_toxic = True
                self.threat_reason = (
                    f"AST MEMBRANE BLOCK: Malicious import detected '{alias.name}'."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] in self.forbidden_modules:
            self.is_toxic = True
            self.threat_reason = (
                f"AST MEMBRANE BLOCK: Malicious from-import detected '{node.module}'."
            )
        self.generic_visit(node)

    def visit_Call(self, node):
        # Prevent dynamic import obfuscation like __import__("os") or eval/exec
        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__", "compile"}:
                self.is_toxic = True
                self.threat_reason = f"AST MEMBRANE BLOCK: Forbidden dynamic execution function '{node.func.id}' detected."
        self.generic_visit(node)


def scan_python_ast(filepath: str) -> tuple[bool, str]:
    """
    The AST Membrane.
    Reads a target Python file and blocks execution if it contains lethal OS-level imports.
    """
    try:
        path = Path(filepath)
        if not path.exists() or path.suffix != ".py":
            return True, ""  # Not a python file, pass to next layer

        code = path.read_text(encoding="utf-8")
        tree = ast.parse(code)

        detector = ToxinDetector()
        detector.visit(tree)

        if detector.is_toxic:
            console.print(
                "\n[bold red]🛑 AST Membrane Triggered: Blocked execution of toxic Python script.[/bold red]"
            )
            return False, detector.threat_reason

        return True, ""
    except SyntaxError:
        return (
            False,
            "AST MEMBRANE ERROR: Script contains invalid Python syntax and cannot be analyzed.",
        )
    except Exception as e:
        return False, f"AST MEMBRANE ERROR: Could not analyze file. {str(e)}"


def scan_python_ast_string(code: str) -> tuple[bool, str]:
    """Scans raw Python strings (like inline -c commands) for lethal imports."""
    try:
        tree = ast.parse(code)
        detector = ToxinDetector()
        detector.visit(tree)

        if detector.is_toxic:
            console.print(
                "\n[bold red]🛑 AST Membrane Triggered: Blocked execution of toxic inline Python script.[/bold red]"
            )
            return False, detector.threat_reason
        return True, ""
    except SyntaxError:
        return False, "AST MEMBRANE ERROR: Inline script contains invalid syntax."
    except Exception as e:
        return False, f"AST MEMBRANE ERROR: Could not analyze inline script. {str(e)}"


def wrap_with_apoptosis(target_script_path: str) -> str:
    """
    CELLULAR APOPTOSIS: Generates a temporary membrane script.
    It installs a strict Python Audit Hook to physically block OS-level execution
    from inside the Python interpreter, then runs the target script.
    """
    membrane_code = f"""
import sys
import runpy

def apoptosis_hook(event, args):
    # The lethal systemic calls we do not allow autonomous agents to execute
    forbidden_events = {{
        "os.system",
        "os.exec",
        "os.posix_spawn",
        "subprocess.Popen",
    }}
    if event in forbidden_events:
        print(f"\\n[APOPTOSIS TRIGGERED] SecurityError: Blocked unauthorized syscall '{{event}}'.", file=sys.stderr)
        sys.exit(1) # Instantly kill the cell

# 1. Install the immune response
sys.addaudithook(apoptosis_hook)

# 2. Execute the Swarm's script inside the membrane
try:
    runpy.run_path("{target_script_path}", run_name="__main__")
except Exception as e:
    print(f"Execution Error: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
    # Write the membrane to a temporary execution file
    temp_dir = Path(tempfile.gettempdir())
    membrane_path = temp_dir / "apoptosis_membrane.py"
    membrane_path.write_text(membrane_code.strip(), encoding="utf-8")

    return str(membrane_path)
