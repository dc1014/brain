# --- System/cli.py ---
import sys
from pathlib import Path
import os
import io
import typer

# Import Biological Modules
from System.cli_cognitive import task, daydream, evolve, forage, compile, absorb
from System.cli_somatic import (
    map_topology,
    status,
    list_reflexes,
    reflex,
    sleep,
    observe,
    sync_mirror,
    imitate,
    watch,
)
from rich.console import Console

# Force Universal UTF-8 Output on Windows
if sys.platform.startswith("win") and "pytest" not in sys.modules:
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except AttributeError:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

console = Console()
app = typer.Typer(
    help="🦾 Brain OS: Biomimetic Agentic Operating System", no_args_is_help=True
)


@app.callback()
def main():
    queue_file = ROOT_DIR / "System" / "execution_queue.json"
    if queue_file.exists():
        if os.environ.get("BRAIN_OS_HEADLESS") == "1":
            raise typer.Exit()


@app.command()
def live():
    """⚡ Synaptic Resonance: Boots the background multi-agent daemons and establishes continuous somatic loops."""
    from System.neuroanatomy.systemic.thymus import ThymusGland

    console.print(
        "[bold green]⚡ Booting Thymus Watchdog & Resuscitating Medulla...[/bold green]"
    )
    thymus = ThymusGland()
    try:
        thymus.boot()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 System interrupt received (Ctrl+C).[/bold red]")
        if thymus.medulla_process and thymus.medulla_process.poll() is None:
            thymus.medulla_process.terminate()


@app.command()
def halt():
    """🛑 Emergency Brake: Instantly kills all active background daemon processes and file watchers."""
    from System.neuroanatomy.autonomic.vagus_nerve import trigger_halt

    trigger_halt()


@app.command()
def recover():
    """🩹 Autonomic Recovery: Reboots the systemic daemons and clears locked memory states."""
    from System.neuroanatomy.autonomic.vagus_nerve import trigger_recover

    trigger_recover()


@app.command()
def approve():
    """✅ Dopaminergic Release: Approves pending tasks waiting in Obsidian."""
    queue_file = ROOT_DIR / "Meta" / "queue.jsonl"
    md_queue = ROOT_DIR / "Meta" / "Pending_Actions.md"
    approved_flag = ROOT_DIR / "Meta" / ".approved"

    if not queue_file.exists() or os.path.getsize(queue_file) == 0:
        console.print(
            "[dim yellow]No pending tasks found in the queue to approve.[/dim yellow]"
        )
        return

    approved_flag.touch()

    if md_queue.exists():
        with open(md_queue, "w", encoding="utf-8") as f:
            f.write(
                "# 🟢 Swarm Action Approved\n*The task has been approved. The Medulla daemon will begin background execution shortly.*\n\n"
            )

    console.print(
        "[bold green]🔓 Inhibition Released: Task approved for execution![/bold green]"
    )


@app.command()
def setup() -> None:
    """Initializes Brain OS using the interactive, high-fidelity Synaptic Genesis onboarding wizard."""
    import asyncio
    from System.core.onboarding.cli import main as run_onboarding

    asyncio.run(run_onboarding())


# Cognitive (CNS)
app.command(name="task")(task)
app.command(name="daydream")(daydream)
app.command(name="evolve")(evolve)
app.command(name="forage")(forage)
app.command(name="compile")(compile)
app.command(name="absorb")(absorb)

# Somatic (Reflexes)
app.command(name="map-topology")(map_topology)
app.command(name="status")(status)
app.command(name="list-reflexes")(list_reflexes)
app.command(name="reflex")(reflex)
app.command(name="sleep")(sleep)

# Cortical Observational Wiring Subcommands
app.command(name="observe")(observe)
app.command(name="sync-mirror")(sync_mirror)
app.command(name="imitate")(imitate)
app.command(name="watch")(watch)

if __name__ == "__main__":
    app()
