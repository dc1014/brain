import typer
import subprocess
import time
from rich.console import Console

import json
import os
import asyncio
from System.neuroanatomy.cortical.prefrontal import execute_pipeline

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
    """
    Global CLI bootloader. Checks for interrupted tasks before running any command.
    """
    if not bootstrap():
        raise typer.Exit(code=1)

    queue_file = ROOT_DIR / "System" / "execution_queue.json"

    # 🧠 PREFRONTAL CORTEX: Autonomic Resume Check
    if queue_file.exists():
        try:
            with open(queue_file, "r", encoding="utf-8") as f:
                queue_data = json.load(f)

            console.print(
                "\n[bold yellow]⚠️ Interrupted Pipeline Detected![/bold yellow]"
            )
            console.print(
                f"[cyan]Pending Task:[/cyan] {queue_data.get('original_task')}"
            )
            console.print(
                f"[cyan]Remaining Steps:[/cyan] {len(queue_data.get('remaining_steps', []))}"
            )

            if os.environ.get("BRAIN_OS_HEADLESS") == "1":
                auth = "y"
            else:
                try:
                    auth = input("\nResume this task? [Y/n]: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    auth = "n"

            if auth in ["", "y", "yes"]:
                console.print("[bold green]Resuming pipeline...[/bold green]\n")

                # ⚡ ZERO-DEBT: Prevent loop collisions inside Pytest/Asyncio runtimes
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    loop.create_task(
                        execute_pipeline(
                            description=queue_data.get("original_task", "Resumed Task"),
                            route_type=queue_data.get("route_type", "WORKSPACE"),
                            domain=queue_data.get("domain", "GENERAL"),
                            resume_pipeline=queue_data.get("remaining_steps"),
                        )
                    )
                else:
                    asyncio.run(
                        execute_pipeline(
                            description=queue_data.get("original_task", "Resumed Task"),
                            route_type=queue_data.get("route_type", "WORKSPACE"),
                            domain=queue_data.get("domain", "GENERAL"),
                            resume_pipeline=queue_data.get("remaining_steps"),
                        )
                    )

                # Halt Typer routing after resume completes or schedules
                raise typer.Exit(code=0)
            else:
                # User declined, clear the stale memory
                if queue_file.exists():
                    os.remove(queue_file)
                console.print("[dim]Stale execution queue cleared.[/dim]\n")
        except typer.Exit:
            # ⚡ Re-raise Typer structural exits so they exit cleanly instead of hitting the raw Exception block
            raise
        except Exception as e:
            console.print(
                f"[bold red]Failed to read execution queue. Corrupted memory purged: {e}[/bold red]"
            )
            if queue_file.exists():
                try:
                    os.remove(queue_file)
                except OSError:
                    pass


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
