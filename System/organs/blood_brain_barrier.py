import os
import re
import ast
from pathlib import Path
from rich.console import Console

console = Console()


def inspect_toxins(command: str) -> tuple[bool, str]:
    """
    The Blood-Brain Barrier.
    Prevents the autonomous installation of external packages during headless/dream states
    to protect against supply-chain poisoning and remote code execution.
    """
    # If a human is actively at the keyboard (not headless), the BBB lets the human decide.
    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
        return True, ""

    # List of toxic patterns that reach out to the internet to download and execute code
    toxin_patterns = [
        r"\bnpm\s+(i|install|add)\b",
        r"\byarn\s+(add)\b",
        r"\bpnpm\s+(add|install)\b",
        r"\bpip\s+install\b",
        r"\buv\s+(add|pip\s+install)\b",
        r"\bbrew\s+install\b",
        r"\bapt(-get)?\s+install\b",
        r"\bcurl\b.*\|.*\b(bash|sh)\b",  # Curl-to-bash scripts
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


# --- NEW: PATH VALIDATION SANDBOX ---
ROOT_DIR = Path(__file__).parent.parent.parent.resolve()


def validate_execution_path(target_path: str) -> tuple[bool, str]:
    """Ensures execution directories are strictly within approved sandboxes."""
    try:
        requested_path = Path(target_path).resolve()

        if not str(requested_path).startswith(str(ROOT_DIR)):
            return (
                False,
                "PATH TRAVERSAL BLOCKED: Attempted to execute outside the OS Root.",
            )

        safe_zones = ["Studio", "Personal", "Professional"]
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
