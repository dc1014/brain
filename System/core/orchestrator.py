import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from System.neuroanatomy.limbic.thalamus import route_sensory_input
from System.core.paths import ROOT_DIR
from System.runtime import execute_pipeline

console = Console()


async def dispatch_task(description: str, obsidian: bool = False) -> None:
    """
    Basal Ganglia / Routing:
    Receives a decomposed sub-task (pulse) from the Prefrontal Cortex.
    Validates it, determines the route, and triggers the Swarm.
    """
    with console.status(
        "[bold yellow]🛡️ Routing pulse through Basal Ganglia...[/bold yellow]",
        spinner="dots",
    ):
        is_valid, reason, route_type, domain, _ = await route_sensory_input(description)

    if not is_valid:
        console.print(
            Panel(f"[bold red]Pulse Rejected:[/bold red] {reason}", border_style="red")
        )
        # ⚡ Throw an exception so the PFC knows to halt the pipeline and prevent cascading hallucinations!
        raise ValueError(f"Pulse rejected by pre-flight validation: {reason}")

    # Execute the validated Swarm route
    await execute_pipeline(description, route_type, domain)


def run_pending_queue() -> None:
    """
    Cognitive Queue Processor:
    Reads pending tasks from Obsidian and feeds them to the Prefrontal Cortex for executive decomposition.
    """
    queue_file = ROOT_DIR / "Meta" / "queue.jsonl"
    pending_file = ROOT_DIR / "Personal" / "pending-tasks.md"

    if not queue_file.exists():
        return

    tasks_to_run = []
    with open(queue_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                tasks_to_run.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not tasks_to_run:
        return

    console.print(
        f"[bold green]🚀 Found {len(tasks_to_run)} pending tasks. Waking Prefrontal Cortex...[/bold green]"
    )

    # Import PFC locally to avoid circular dependencies during boot
    from System.neuroanatomy.cortical.prefrontal import PrefrontalCortex

    pfc = PrefrontalCortex()

    for idx, task_obj in enumerate(tasks_to_run, 1):
        console.print(
            f"\n[bold blue]--- Processing Queue Item {idx}/{len(tasks_to_run)} ---[/bold blue]"
        )
        task_desc = task_obj.get("prompt")
        if not task_desc:
            continue

        try:
            # ⚡ SHIFT-LEFT: Hand the massive queued task to the PFC to supervise!
            asyncio.run(pfc.execute_goal(task_desc))
        except Exception as e:
            console.print(f"[bold red]Queue Task Failed:[/bold red] {str(e)}")

    # Wipe the queue after processing
    with open(queue_file, "w", encoding="utf-8") as f:
        f.write("")

    if pending_file.exists():
        with open(pending_file, "w", encoding="utf-8") as f:
            f.write("# ⚠️ Pending Execution Queue\n\n*Queue is currently empty.*")
