import typer
import subprocess
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.core.boot import bootstrap
from System.core.orchestrator import run_pending_queue

# --- Biological Module Imports (Re-exported for the Test Suite) ---
from System.cli_cognitive import task, daydream, evolve, forage
from System.cli_somatic import map_topology, status, list_reflexes, reflex, sleep

console = Console()
app = typer.Typer(
    help="🦾 Brain OS: Biomimetic Agentic Operating System", no_args_is_help=True
)


@app.callback()
def main():
    """The Polymerase Boot Sequence runs on every command execution."""
    if not bootstrap():
        raise typer.Exit(code=1)


@app.command()
def init():
    """Initializes the Brain OS environment and biological structures."""
    bootstrap()

    (ROOT_DIR / "Meta").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "Meta" / "global-memory.md").touch(exist_ok=True)

    (ROOT_DIR / "Studio").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "Studio" / "studio-memory.md").touch(exist_ok=True)

    (ROOT_DIR / "Personal").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "Personal" / "personal-memory.md").touch(exist_ok=True)

    (ROOT_DIR / "Professional").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "Professional" / "professional-memory.md").touch(exist_ok=True)

    subprocess.run(["git", "init"], cwd=ROOT_DIR, capture_output=True)

    git_dir = ROOT_DIR / ".git"
    hooks_dir = ROOT_DIR / "scripts" / "githooks"
    if git_dir.exists() and hooks_dir.exists():
        subprocess.run(
            ["git", "config", "core.hooksPath", "scripts/githooks"],
            cwd=ROOT_DIR,
            capture_output=True,
        )
        subprocess.run(
            ["git", "update-index", "--chmod=+x", "scripts/githooks/pre-commit"],
            cwd=ROOT_DIR,
            capture_output=True,
        )
        console.print(f"[dim]Secured Git hooks for repository: {ROOT_DIR.name}[/dim]")

    # ⚡ SHIFT-LEFT: Autonomously seed the visual cortex (Playwright binaries)
    console.print("[dim]Seeding Occipital/Web Receptor binaries (Chromium)...[/dim]")
    try:
        subprocess.run(
            ["uv", "run", "playwright", "install", "chromium"],
            cwd=ROOT_DIR,
            capture_output=True,
            check=True,
        )
        console.print("[dim]Chromium visual cortex seeded successfully.[/dim]")
    except subprocess.CalledProcessError as e:
        console.print(
            f"[bold red]Failed to seed Chromium: {e.stderr.decode()}[/bold red]"
        )

    console.print("[bold green]🧠 Brain OS Initialized Successfully.[/bold green]")


@app.command()
def execute_pending():
    """Executes all pending tasks in the Obsidian / jsonl queue."""
    run_pending_queue()


# ==============================================================================
# ROUTE INJECTION (Preserving Flat UX & Test Imports)
# ==============================================================================

# Cognitive (CNS)
app.command(name="task")(task)
app.command(name="daydream")(daydream)
app.command(name="evolve")(evolve)
app.command(name="forage")(forage)

# Somatic (Reflexes)
app.command(name="map-topology")(map_topology)
app.command(name="status")(status)
app.command(name="list-reflexes")(list_reflexes)
app.command(name="reflex")(reflex)
app.command(name="sleep")(sleep)

if __name__ == "__main__":
    app()
