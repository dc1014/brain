import asyncio
import typer
import shutil
from rich.console import Console
from System.core.paths import ROOT_DIR
from System.core.orchestrator import dispatch_task
from System.runtime import execute_pipeline

console = Console()


def task(
    prompt: str = typer.Argument(..., help="The cognitive task to execute."),
    obsidian: bool = typer.Option(
        False,
        "--obsidian",
        help="Route to the pending queue instead of immediate execution.",
    ),
):
    """Executes a cognitive task via the Prefrontal Cortex."""
    asyncio.run(dispatch_task(prompt, obsidian=obsidian))


def daydream(
    domain: str = typer.Option("PERSONAL", "--domain", help="Domain context for DMN."),
):
    """Default Mode Network (DMN): Background processing and memory consolidation."""
    console.print(f"[blue]☁️  Entering Daydream state for {domain}...[/blue]")
    asyncio.run(
        execute_pipeline(
            "Run Default Mode Network background processing.",
            "SUBCONSCIOUS_DAYDREAM",
            domain,
        )
    )


def evolve():
    """Triggers self-improvement and codebase evolution routines."""
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
    topic: str = typer.Argument(..., help="The topic to research."),
    domain: str = typer.Option(
        "STUDIO", "--domain", help="Domain context for foraging."
    ),
):
    """Information foraging and web scraping for a specific topic."""
    console.print(f"[green]🌿 Foraging for information on:[/green] {topic} in {domain}")
    asyncio.run(
        execute_pipeline(
            f"Forage the web and build a comprehensive research dossier on: {topic}",
            "SUBCONSCIOUS_FORAGE",
            domain,
        )
    )
