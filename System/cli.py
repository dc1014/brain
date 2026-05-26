# ruff: noqa: E402
# --- System/cli.py ---
import io
import json
import os
import shutil
import sys
import traceback
import warnings
from pathlib import Path

# Suppress noisy third-party provider warnings (like LiteLLM / AWS Bedrock)
# before importing any downstream cognitive modules that trigger them.
os.environ.setdefault("LITELLM_LOG", "ERROR")
os.environ.setdefault("LITELLM_TELEMETRY", "False")
os.environ.setdefault("SUPPRESS_LITELLM_WARNINGS", "True")
warnings.filterwarnings("ignore", category=UserWarning, module="litellm")
warnings.filterwarnings("ignore", message=".*botocore.*")
warnings.filterwarnings("ignore", message=".*boto3.*")

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

# Standalone Sensory Package Route Mapping Proxy Ingestion Handles
from Sense.receptors.audio import play_audio, record_audio
from Sense.receptors.taste import sample_file
from Sense.receptors.vision import take_screenshot
from Sense.receptors.web import transduce_web_page

# Import domain function blocks
from System.cli_somatic import (
    assimilate,
    expose_dermis,
    imitate,
    list_reflexes,
    map_topology,
    observe,
    reflex,
    sleep,
    status,
    sync_mirror,
    watch,
)
from System.core.concurrency import lock_concurrency_defaults
from System.core.file_transaction import read_state_sync
from System.neuroanatomy.sensory.olfactory import process_scent_profile

# Secure prioritize root folder mapping
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Lock process allocations before parallel sequences wake
lock_concurrency_defaults()

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

console = Console()


def graceful_coretex_excepthook(exc_type, exc_value, exc_traceback):
    if exc_type.__name__ == "Exit" or exc_type is SystemExit:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception_only(exc_type, exc_value)).strip()
    console.print()
    console.print(
        Panel(
            f"[bold white]{error_msg}[/bold white]\n\n[dim]The Vagus Nerve has safely preserved your environment state.[/dim]",
            title="[bold red]CORTICAL INTERRUPT[/bold red]",
            border_style="red",
            expand=False,
        )
    )
    sys.exit(1)


sys.excepthook = graceful_coretex_excepthook

# Master Typer Configuration
app = typer.Typer(
    help="CoreTex OS: Biomimetic Agentic Operating System", no_args_is_help=True
)

# Sub-App Domain Subcommands
cognitive_app = typer.Typer(help="Cognitive Commands (CNS Execution Pathways)")
somatic_app = typer.Typer(help="Somatic Commands (Autonomic Reflex Arcs)")
sense_app = typer.Typer(help="Sensory Commands (Exteroceptive Organ Ingestion Handles)")

app.add_typer(cognitive_app, name="cognitive")
app.add_typer(somatic_app, name="somatic")
app.add_typer(sense_app, name="sense")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose systemic logging for daemons and reflexes",
    ),
):
    """Global configuration check parameters."""
    if verbose:
        os.environ["CORETEX_VERBOSE"] = "1"
        console.print(
            "[dim cyan]Verbose sensory mode enabled. Somatic logging active.[/dim cyan]"
        )

    queue_file = ROOT_DIR / "System" / "execution_queue.json"
    queue_data = read_state_sync(queue_file, default_factory=dict)
    if queue_data and os.environ.get("CORETEX_HEADLESS") == "1":
        raise typer.Exit()


# ==============================================================================
# TOP-LEVEL CORE LIFECYCLE MANAGEMENT COMMANDS
# ==============================================================================


@app.command()
def setup() -> None:
    """Initializes CoreTex OS using the interactive, high-fidelity Synaptic Genesis onboarding wizard."""
    import asyncio
    from System.core.onboarding.genesis import main as run_onboarding

    asyncio.run(run_onboarding())


@app.command()
def live():
    """Synaptic Resonance: Boots background multi-agent daemons and establishes continuous somatic loops."""
    from System.neuroanatomy.systemic.thymus import ThymusGland

    console.print(
        "[bold green]Booting Thymus Watchdog & Resuscitating Medulla...[/bold green]"
    )
    thymus = ThymusGland()
    try:
        thymus.boot()
    except KeyboardInterrupt:
        console.print("\n[bold red]System interrupt received (Ctrl+C).[/bold red]")
        if thymus.medulla_process and thymus.medulla_process.poll() is None:
            thymus.medulla_process.terminate()


@app.command()
def halt():
    """Emergency Brake: Instantly kills all active background daemon processes and file watchers."""
    from System.neuroanatomy.autonomic.vagus_nerve import trigger_halt

    trigger_halt()


@app.command()
def recover():
    """Autonomic Recovery: Reboots the systemic daemons and clears locked memory states."""
    from System.neuroanatomy.autonomic.vagus_nerve import trigger_recover

    trigger_recover()


@app.command()
def approve():
    """Dopaminergic Release: Approves pending agentic tasks waiting in the workspace."""
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
                "# Swarm Action Approved\n*The task has been approved. The Medulla daemon will begin background execution shortly.*\n\n"
            )
    console.print(
        "[bold green]Inhibition Released: Task approved for execution![/bold green]"
    )


@app.command()
def destroy() -> None:
    """Systemic Apoptosis: Zero-Residue Uninstaller to completely purge local logs and configurations."""
    console.print(
        "[bold red]WARNING: You are about to initiate Systemic Apoptosis.[/bold red]"
    )
    console.print(
        "This will permanently erase all memory ledgers, token usage logs, and environment API keys."
    )

    if not Confirm.ask(
        "Are you absolutely sure you want to destroy CoreTex OS?", default=False
    ):
        console.print("[dim green]Apoptosis aborted. The OS survives.[/dim green]")
        return

    with console.status("[red]Executing Zero-Residue sequence...[/red]"):
        log_dir = ROOT_DIR / "logs"
        if log_dir.exists():
            shutil.rmtree(log_dir, ignore_errors=True)
            console.print(
                "[dim]Deleted episodic ledgers, token tracking, and system logs.[/dim]"
            )

        env_file = ROOT_DIR / ".env"
        if env_file.exists():
            env_file.unlink()
            console.print("[dim]Deleted environment credentials and API keys.[/dim]")

        queue_file = ROOT_DIR / "System" / "execution_queue.json"
        if queue_file.exists():
            queue_file.unlink()
            console.print("[dim]Flushed pending motor execution queues.[/dim]")

    console.print(
        "\n[bold green]Systemic Apoptosis complete. CoreTex OS has been purged.[/bold green]"
    )


# ==============================================================================
# LAZY COMMAND WRAPPERS
# ==============================================================================


def task(*args, **kwargs):
    from System.cli_cognitive import task as _task

    return _task(*args, **kwargs)


def daydream(*args, **kwargs):
    from System.cli_cognitive import daydream as _daydream

    return _daydream(*args, **kwargs)


def evolve(*args, **kwargs):
    from System.cli_cognitive import evolve as _evolve

    return _evolve(*args, **kwargs)


def forage(*args, **kwargs):
    from System.cli_cognitive import forage as _forage

    return _forage(*args, **kwargs)


def compile(*args, **kwargs):
    from System.cli_cognitive import compile as _compile

    return _compile(*args, **kwargs)


def absorb(*args, **kwargs):
    from System.cli_cognitive import absorb as _absorb

    return _absorb(*args, **kwargs)


# ==============================================================================
# DUAL REGISTRATION MATRIX (Unhidden to expose shortcuts in root help menu)
# ==============================================================================


# Cognitive Registry Hooks
@cognitive_app.command(name="task")
@app.command(name="task")
def run_task(
    description: str = typer.Argument(
        ..., help="The objective for the Swarm to accomplish."
    ),
    domain: str = typer.Option(
        "AUTO", help="The environmental domain (e.g., STUDIO, PERSONAL)."
    ),
    route: str = typer.Option(
        "AUTO", help="The targeted neuro-route (e.g., WORKSPACE, TERMINAL)."
    ),
    obsidian: bool = typer.Option(
        False,
        "--obsidian",
        help="Queues the task into Obsidian instead of running immediately.",
    ),
):
    """🧠 Engages the Prefrontal Cortex to execute a cognitive task."""
    task(description=description, domain=domain, route=route, obsidian=obsidian)


@cognitive_app.command(name="daydream")
@app.command(name="daydream")
def run_daydream(
    topic: str = typer.Argument(
        None,
        help="An optional topic or theme to anchor the Daydreamer's cognitive focus.",
    ),
    domain: str = typer.Option(
        None, "--domain", "-d", help="Explicitly scope the daydream destination vault."
    ),
):
    """🌌 Activates the Default Mode Network to process thoughts and generate strategic insights."""
    daydream(topic=topic, domain=domain)


@cognitive_app.command(name="evolve")
@app.command(name="evolve")
def run_evolve():
    """🧬 Analyzes System/logs and codebase evolution routines."""
    evolve()


@cognitive_app.command(name="forage")
@app.command(name="forage")
def run_forage(
    topic: str = typer.Argument(..., help="The search query or URL to forage."),
    domain: str = typer.Option(
        "GENERAL", help="The environmental domain (e.g., STUDIO)."
    ),
):
    """Information foraging and web scraping for a specific topic."""
    forage(topic=topic, domain=domain)


@cognitive_app.command(name="compile")
@app.command(name="compile")
def run_compile():
    """⚙️ Compiles the most recent successful memory into a Zero-Token Engram."""
    compile()


@cognitive_app.command(name="absorb")
@app.command(name="absorb")
def run_absorb(
    path: Path = typer.Argument(
        ..., help="Path to the folder, codebase, or file to absorb into memory."
    ),
    domain: str = typer.Option(
        "Personal", "--domain", "-d", help="Target domain segment."
    ),
    tags: str = typer.Option(
        None, "--tags", "-t", help="Comma-separated conceptual metadata labels."
    ),
):
    """🧫 Phagocytosis: Ingests external data, codebases, or documents into long-term structures."""
    absorb(path=path, domain=domain, tags=tags)


# Somatic Registry Hooks
somatic_app.command(name="map-topology")(map_topology)
somatic_app.command(name="status")(status)
somatic_app.command(name="list-reflexes")(list_reflexes)
somatic_app.command(name="reflex")(reflex)
somatic_app.command(name="sleep")(sleep)
somatic_app.command(name="assimilate")(assimilate)
somatic_app.command(name="watch")(watch)
somatic_app.command(name="observe")(observe)
somatic_app.command(name="sync-mirror")(sync_mirror)
somatic_app.command(name="imitate")(imitate)
somatic_app.command(name="expose-dermis")(expose_dermis)

app.command(name="map-topology")(map_topology)
app.command(name="status")(status)
app.command(name="list-reflexes")(list_reflexes)
app.command(name="reflex")(reflex)
app.command(name="sleep")(sleep)
app.command(name="assimilate")(assimilate)
app.command(name="watch")(watch)
app.command(name="observe")(observe)
app.command(name="sync-mirror")(sync_mirror)
app.command(name="imitate")(imitate)
app.command(name="expose-dermis")(expose_dermis)


# Standalone Sensory Package Route Mapping Proxy Ingestion Handles
@sense_app.command(name="scrape")
@app.command(name="scrape")
def sense_scrape(url: str = typer.Argument(..., help="Web link target URL.")):
    try:
        result = transduce_web_page(url)
        print(result)
        if "<sensory_error" in result:
            sys.stderr.write(result + "\n")
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(
            f'<sensory_error source="{url}">\n{str(e)}\n</sensory_error>\n'
        )
        sys.exit(1)


@sense_app.command(name="screenshot")
@app.command(name="screenshot")
def sense_screenshot(url: str, output: str = "screenshot.png"):
    console.print(take_screenshot(url, output))


@sense_app.command(name="perceive")
@app.command(name="perceive")
def sense_perceive(
    image_path: str, query: str = "Describe this image in extreme detail."
):
    from System.neuroanatomy.cortical.occipital import perceive_image

    console.print(perceive_image(image_path, query))


@sense_app.command(name="listen")
@app.command(name="listen")
def sense_listen(duration: int = 5, output: str = "recording.wav"):
    target = Path(output)
    out_path = (
        ROOT_DIR / "Media" / "Recordings" / output
        if target.parent == Path(".")
        else target.resolve()
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    console.print(
        f"[bold cyan]Hardware Mic Active: Recording for {duration} seconds...[/bold cyan]"
    )
    console.print(f"[green]{record_audio(str(out_path), duration)}[/green]")


@sense_app.command(name="speak")
@app.command(name="speak")
def sense_speak(file: str):
    target = Path(file).resolve()
    if not target.exists():
        console.print(f"[bold red]File not found: {file}[/bold red]")
        return
    console.print(f"[bold cyan]Physical Speaker Active: Playing {file}...[/bold cyan]")
    play_audio(str(target))


@sense_app.command(name="smell")
@app.command(name="smell")
def sense_smell(directory: str = "Studio"):
    console.print(
        f"[bold cyan]Olfactory Bulb smelling '{directory}' for anomalies...[/bold cyan]"
    )
    if "status='clean'" in process_scent_profile(directory):
        console.print("[bold green]Vault smells clean. No rot detected.[/bold green]")
    else:
        console.print(
            "[bold yellow]Anomalies Detected! Scent report written to Meta/Olfactory_Anomalies.md[/bold yellow]"
        )


@sense_app.command(name="taste")
@app.command(name="taste")
def sense_taste(filepath: str):
    console.print_json(json.dumps(sample_file(filepath)))


@sense_app.command(name="flush")
@app.command(name="flush")
def sense_flush():
    from System.neuroanatomy.systemic.lymphatic import flush_waste

    flush_waste()


@sense_app.command(name="purge")
@app.command(name="purge")
def sense_purge():
    from System.neuroanatomy.systemic.lymphatic import purge_waste

    purge_waste()


if __name__ == "__main__":
    app()
