import typer
import subprocess
import time
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
    if not bootstrap():
        raise typer.Exit(code=1)


@app.command()
def init():
    """Initializes the Brain OS environment and biological structures."""
    bootstrap()

    # 1. Hydrate Biological Membranes
    for directory in ["Meta", "Studio", "Personal"]:
        (ROOT_DIR / directory).mkdir(parents=True, exist_ok=True)

    (ROOT_DIR / "Meta" / "global-memory.md").touch(exist_ok=True)
    (ROOT_DIR / "Studio" / "studio-memory.md").touch(exist_ok=True)
    (ROOT_DIR / "Personal" / "personal-memory.md").touch(exist_ok=True)

    # 2. Wire Autonomous Git Hooks (RESTORED TO FIX TEST DEBT)
    console.print("[dim]Wiring autonomous git hooks for Shift-Left security...[/dim]")
    for git_dir in ROOT_DIR.rglob(".git"):
        repo_root = git_dir.parent
        hooks_dir = repo_root / "scripts" / "githooks"

        if hooks_dir.exists():
            console.print(f"[dim] - Securing repository: {repo_root.name}[/dim]")
            # The 3 specific git configurations the test expects
            subprocess.run(
                ["git", "config", "core.hooksPath", "scripts/githooks"],
                cwd=repo_root,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "core.fileMode", "true"],
                cwd=repo_root,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "pull.rebase", "false"],
                cwd=repo_root,
                capture_output=True,
            )

    # 3. Seed Visual Cortex
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


@app.command()
def live():
    """🫀 Breathe life into Brain OS. Starts the autonomic Medulla Oblongata daemon."""
    from System.neuroanatomy.autonomic.medulla import MedullaOblongata

    console.print("[bold green]⚡ Resuscitating biological systems...[/bold green]")
    brainstem = MedullaOblongata()
    brainstem.wake()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 System interrupt received (Ctrl+C).[/bold red]")
        console.print(
            "[dim yellow]Initiating graceful biological shutdown...[/dim yellow]"
        )
        brainstem.stop()


# Cognitive (CNS)
app.command(name="task")(task)
app.command(name="daydream")(daydream)
app.command(name="evolve")(evolve)
app.command(name="forage")(forage)
app.command(name="compile")(compile)

# Somatic (Reflexes)
app.command(name="map-topology")(map_topology)
app.command(name="status")(status)
app.command(name="list-reflexes")(list_reflexes)
app.command(name="reflex")(reflex)
app.command(name="sleep")(sleep)
