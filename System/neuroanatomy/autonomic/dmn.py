import subprocess
from pathlib import Path
from datetime import datetime
from rich.console import Console
from System.core.paths import ROOT_DIR

console = Console()


def generate_dream_branch_name() -> str:
    """Generates a timestamped branch name for the dream state."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"dream/hypothesis_{timestamp}"


def _get_current_branch(target_dir: Path) -> str:
    """Identifies the current active branch before sleep."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return "main"


def enforce_rem_paralysis(project_name: str) -> tuple[str | None, str | None]:
    """
    Traps the AI in an isolated Git branch before it starts writing code.
    Returns (dream_branch_name, original_branch_name) if successful.
    """
    target_dir = ROOT_DIR / "Studio" / project_name

    if not target_dir.exists():
        console.print(
            f"[bold red]Cannot dream in {project_name}. Directory not found.[/bold red]"
        )
        return None, None

    # Check if it's a git repo safely
    is_repo = subprocess.run(
        ["git", "status"], cwd=str(target_dir), capture_output=True
    )
    if is_repo.returncode != 0:
        console.print(
            f"[bold red]REM Paralysis failed: {project_name} is not a Git repository. Aborting dream to prevent reality corruption.[/bold red]"
        )
        return None, None

    orig_branch = _get_current_branch(target_dir)
    branch_name = generate_dream_branch_name()

    # Isolate reality
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        console.print(
            f"[bold magenta]🧠 REM Paralysis Active: AI is safely sandboxed in branch '{branch_name}'.[/bold magenta]"
        )
        return branch_name, orig_branch
    else:
        console.print(
            f"[bold red]Failed to enter REM sleep: {result.stderr}[/bold red]"
        )
        return None, None


def wake_from_rem(project_name: str, dream_branch: str, original_branch: str) -> None:
    """Commits the dream hypothesis and safely restores reality back to the original branch."""
    target_dir = ROOT_DIR / "Studio" / project_name
    if not target_dir.exists():
        return

    console.print(
        "[bold yellow]☀️ Waking from REM sleep. Consolidating dream state...[/bold yellow]"
    )

    # 1. Stage all hallucinated changes
    subprocess.run(["git", "add", "."], cwd=str(target_dir), capture_output=True)

    # 2. Commit the dream
    subprocess.run(
        ["git", "commit", "-m", f"Autonomic Dream Sequence: {dream_branch}"],
        cwd=str(target_dir),
        capture_output=True,
    )

    # 3. Restore Reality
    res = subprocess.run(
        ["git", "checkout", original_branch],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
    )

    if res.returncode == 0:
        console.print(
            f"[bold green]✨ Reality Restored. Active branch is back to '{original_branch}'. The dream is saved in '{dream_branch}'.[/bold green]"
        )
    else:
        console.print(
            f"[bold red]⚠️ Wake Error: Failed to restore branch '{original_branch}'. {res.stderr}[/bold red]"
        )


def trigger_daydreams() -> None:
    """
    The Default Mode Network entry point for sleep cycles.
    Invoked by the Pineal Gland during idle periods.
    """
    console.print(
        "\n[dim magenta]🧠 DMN: Scanning for projects to optimize during REM sleep...[/dim magenta]"
    )
    # The architecture is now secure. In the future, the Swarm will be injected here.
    console.print(
        "[dim magenta]🧠 DMN: No active deep-sleep hypothesis configured. Resting.[/dim magenta]"
    )
