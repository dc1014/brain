import asyncio
import json
import os
import typer
import shutil
import time

from rich.console import Console
from System.core.paths import ROOT_DIR
from System.neuroanatomy.cortical.prefrontal import execute_pipeline

console = Console()


def task(
    description: str = typer.Argument(
        ..., help="The objective for the Swarm to accomplish."
    ),
    domain: str = typer.Option(
        "GENERAL", help="The environmental domain (e.g., STUDIO, PERSONAL)."
    ),
    route: str = typer.Option(
        "WORKSPACE", help="The targeted neuro-route (e.g., WORKSPACE, TERMINAL)."
    ),
    obsidian: bool = typer.Option(
        False,
        "--obsidian",
        help="Queues the task into Obsidian instead of running immediately.",
    ),
):
    """🧠 Engages the Prefrontal Cortex to execute a cognitive task."""

    if obsidian:
        # Route to queue instead of executing
        queue_file = ROOT_DIR / "Meta" / "queue.jsonl"
        pending_file = ROOT_DIR / "Personal" / "pending-tasks.md"

        queue_file.parent.mkdir(parents=True, exist_ok=True)
        pending_file.parent.mkdir(parents=True, exist_ok=True)

        with open(queue_file, "a", encoding="utf-8") as f:
            f.write(
                json.dumps({"prompt": description, "route": route, "domain": domain})
                + "\n"
            )

        with open(pending_file, "a", encoding="utf-8") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            f.write(
                f"### ⏳ Pending Task ({timestamp})\n**Prompt:** {description}\n---\n"
            )

        console.print(
            "[bold green]✅ Task safely queued into Obsidian vault![/bold green]"
        )
        return

    from System.neuroanatomy.cortical.prefrontal import PrefrontalCortex

    pfc = PrefrontalCortex()
    asyncio.run(pfc.execute_goal(description, domain, route))


def daydream():
    """🌌 Activates the Default Mode Network to process idle thoughts."""
    from System.neuroanatomy.autonomic.dmn import trigger_daydreams

    trigger_daydreams()


def evolve():
    """🧬 Analyzes System/logs and codebase evolution routines."""
    console.print("[magenta]🧬 Triggering Evolutionary Algorithms...[/magenta]")

    agents_file = ROOT_DIR / "System" / "config" / "agents.yaml"
    mutations_file = ROOT_DIR / "Meta" / "Mutations.md"

    if agents_file.exists():
        shutil.copy2(agents_file, agents_file.with_suffix(".yaml.bak"))
        if mutations_file.exists():
            mutation_content = mutations_file.read_text(encoding="utf-8")
            if "<neuroplasticity" in mutation_content:
                agents_data = agents_file.read_text(encoding="utf-8")
                agents_file.write_text(
                    agents_data
                    + f"\n# <neuroplastic_rule applied>\n{mutation_content}\n",
                    encoding="utf-8",
                )

    asyncio.run(
        execute_pipeline(
            "Analyze the codebase and suggest evolutionary structural improvements.",
            "FORGE",
            "STUDIO",
        )
    )


def forage(
    topic: str = typer.Argument(..., help="The search query or URL to forage."),
    domain: str = typer.Option(
        "GENERAL", help="The environmental domain (e.g., STUDIO)."
    ),
):
    """Information foraging and web scraping for a specific topic."""
    os.environ["BRAIN_OS_HEADLESS"] = "1"
    console.print(f"[green]🌿 Foraging for information on:[/green] {topic} in {domain}")
    asyncio.run(
        execute_pipeline(
            f"Search the web and gather comprehensive information about: {topic}",
            "WEB",
            domain,
        )
    )


def compile():
    """⚙️ Compiles the most recent successful memory into a Zero-Token Engram."""
    from System.neuroanatomy.limbic.episodic import MEMORY_FILE
    from System.neuroanatomy.autonomic.cerebellum import CerebellarCompiler
    import json

    if not MEMORY_FILE.exists():
        console.print("[bold red]No episodic memory found to compile.[/bold red]")
        return

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            episodes = [json.loads(line) for line in f if line.strip()]

        successful_episodes = [
            ep for ep in episodes if "Success" in ep.get("outcome", "")
        ]

        if not successful_episodes:
            console.print(
                "[bold yellow]No successful episodes found in recent memory.[/bold yellow]"
            )
            return

        latest = successful_episodes[-1]
        telemetry = f"Steps executed: {', '.join(latest['tasks_executed'])}"

        compiler = CerebellarCompiler()
        compiler.compile_engram(latest["objective"], telemetry)

    except Exception as e:
        console.print(
            f"[bold red]Failed to access memory for compilation: {e}[/bold red]"
        )
