import subprocess
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

# Define the absolute root of the Brain OS
ROOT_DIR: Path = Path(__file__).parent.parent.resolve()

# The AI can see everything, but can ONLY write to these specific folders
ALLOWED_DIRECTORIES: set[Path] = {
    ROOT_DIR / "Personal",
    ROOT_DIR / "Professional",
    ROOT_DIR / "Studio",
    ROOT_DIR / "Meta",
}

console = Console()


def is_safe_path(target_path: Path) -> bool:
    """Check if the target path strictly resides within allowed directories."""
    resolved_target = target_path.resolve()
    for allowed_dir in ALLOWED_DIRECTORIES:
        try:
            resolved_target.relative_to(allowed_dir)
            return True
        except ValueError:
            continue
    return False


def write_safe_file(filepath: str, content: str) -> str:
    """Writes files safely, blocking writes outside the sandbox."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to write at {target_path}."

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return f"SUCCESS: File safely written to {target_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to write file - {str(e)}"


def read_safe_file(filepath: str) -> str:
    """Reads the contents of a file within the safe zones."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to read at {target_path}."
        if not target_path.exists():
            return f"ERROR: File not found at {target_path.relative_to(ROOT_DIR)}"
        if not target_path.is_file():
            return "ERROR: Target is not a file."
        return target_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"ERROR: Failed to read file - {str(e)}"


def list_safe_directory(directory_path: str) -> str:
    """Lists all files and folders inside a safe directory."""
    try:
        target_path: Path = (ROOT_DIR / directory_path).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to list directory at {target_path}."
        if not target_path.exists() or not target_path.is_dir():
            return f"ERROR: Directory not found at {target_path.relative_to(ROOT_DIR)}"

        items = []
        for item in target_path.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{item_type}] {item.name}")
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"ERROR: Failed to list directory - {str(e)}"


def rename_safe_file(old_filepath: str, new_filepath: str) -> str:
    """Renames or moves a file within the safe zones."""
    try:
        old_path: Path = (ROOT_DIR / old_filepath).resolve()
        new_path: Path = (ROOT_DIR / new_filepath).resolve()

        if not is_safe_path(old_path) or not is_safe_path(new_path):
            return "SECURITY BLOCK: Access denied. Source and dest must be safe."
        if not old_path.exists():
            return f"ERROR: File not found at {old_path.relative_to(ROOT_DIR)}"

        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)
        return f"SUCCESS: Renamed to {new_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to rename file - {str(e)}"


def append_safe_file(filepath: str, content: str) -> str:
    """Appends content safely, injecting before </working_memory> if present."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to append at {target_path}."

        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content + "\n", encoding="utf-8")
            return f"SUCCESS: File appended at {target_path.relative_to(ROOT_DIR)}"

        current_text = target_path.read_text(encoding="utf-8")
        if "</working_memory>" in current_text:
            new_text = current_text.replace(
                "</working_memory>", f"{content}\n</working_memory>"
            )
            target_path.write_text(new_text, encoding="utf-8")
            return f"SUCCESS: Content injected into {target_path.relative_to(ROOT_DIR)}"

        with open(target_path, "a", encoding="utf-8") as f:
            f.write("\n" + content + "\n")
        return f"SUCCESS: Content appended to {target_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to append to file - {str(e)}"


def bootstrap_project(
    project_name: str, template_url: str = "https://github.com/dc1014/forge.git"
) -> str:
    """Clones a project archetype into the Studio directory."""
    try:
        target_path: Path = (ROOT_DIR / "Studio" / project_name).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to clone into {target_path}."
        if target_path.exists():
            return f"ERROR: Directory exists at {target_path.relative_to(ROOT_DIR)}"

        result = subprocess.run(
            ["git", "clone", template_url, str(target_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return f"SUCCESS: Bootstrapped at {target_path.relative_to(ROOT_DIR)}"
        return f"ERROR: Git clone failed - {result.stderr}"
    except Exception as e:
        return f"ERROR: Failed to bootstrap project - {str(e)}"


def execute_command(command: str, directory_path: str) -> str:
    """
    Executes a shell command. Yields I/O to terminal for HITL downstream processes.
    Enforces Shift-Left explicit approval before execution.
    """
    try:
        target_path: Path = (ROOT_DIR / directory_path).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to execute in {target_path}."
        if not target_path.exists() or not target_path.is_dir():
            return f"ERROR: Directory not found at {target_path.relative_to(ROOT_DIR)}"

        console.print("\n[bold red]⚠️  SECURITY ALERT: EXECUTION REQUESTED[/bold red]")
        is_approved = Confirm.ask(
            f"[yellow]Brain OS wants to run:[/yellow] '{command}'\n"
            f"[yellow]in directory:[/yellow] '{target_path.relative_to(ROOT_DIR)}'\n"
            f"[bold]Allow execution?[/bold]"
        )

        if not is_approved:
            return "SECURITY BLOCK: User explicitly denied command execution."

        console.print(f"[dim]Executing '{command}'... (Terminal I/O mapped)[/dim]\n")

        # Subprocess without capture_output maps stdin/stdout straight to terminal
        result = subprocess.run(command, shell=True, cwd=target_path)
        console.print(
            f"\n[dim]Execution completed with exit code {result.returncode}[/dim]"
        )

        if result.returncode == 0:
            return f"SUCCESS: Command '{command}' executed successfully."
        return f"ERROR: Command failed with exit code {result.returncode}."
    except Exception as e:
        return f"ERROR: Failed to execute command - {str(e)}"
