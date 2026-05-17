import subprocess
from datetime import datetime
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent


def generate_dream_branch_name() -> str:
    """Generates a timestamped branch name for the dream state."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"dream/hypothesis_{timestamp}"


def enforce_rem_paralysis(project_name: str) -> str | None:
    """
    Traps the AI in an isolated Git branch before it starts writing code.
    Returns the branch name if successful, None if it fails.
    """
    target_dir = ROOT_DIR / "Studio" / project_name

    if not target_dir.exists():
        console.print(
            f"[bold red]Cannot dream in {project_name}. Directory not found.[/bold red]"
        )
        return None

    # Check if it's a git repo
    is_repo = subprocess.run(["git", "status"], cwd=target_dir, capture_output=True)
    if is_repo.returncode != 0:
        console.print(
            f"[bold red]REM Paralysis failed: {project_name} is not a Git repository. Aborting dream to prevent reality corruption.[/bold red]"
        )
        return None

    branch_name = generate_dream_branch_name()

    # Isolate reality
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=target_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        console.print(
            f"[bold magenta]🧠 REM Paralysis Active: AI is safely sandboxed in branch '{branch_name}'.[/bold magenta]"
        )
        return branch_name
    else:
        console.print(
            f"[bold red]Failed to enter REM sleep: {result.stderr}[/bold red]"
        )
        return None
