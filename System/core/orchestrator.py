import asyncio
import json
import os
from rich.console import Console
from rich.panel import Panel
from System.neuroanatomy.limbic.thalamus import route_sensory_input
from System.core.paths import ROOT_DIR
from System.neuroanatomy.cortical.prefrontal import execute_pipeline

console = Console()


async def dispatch_task(description: str, obsidian: bool = False) -> None:
    with console.status(
        "[bold yellow]🛡️ Routing pulse through Basal Ganglia...[/bold yellow]",
        spinner="dots",
    ):
        is_valid, reason, route_type, domain, _ = await route_sensory_input(description)

    if not is_valid:
        console.print(
            Panel(f"[bold red]Pulse Rejected:[/bold red] {reason}", border_style="red")
        )
        raise ValueError(f"Pulse rejected by pre-flight validation: {reason}")

    await execute_pipeline(description, route_type, domain)


def run_pending_queue() -> None:
    """
    Cognitive Queue Processor:
    Reads pending tasks, checks for dopamine release flags, and executes them.
    """
    queue_file = ROOT_DIR / "Meta" / "queue.jsonl"
    pending_file = ROOT_DIR / "Meta" / "Pending_Actions.md"
    approved_flag = ROOT_DIR / "Meta" / ".approved"

    # ⚡ THE FIX: If there is no explicit .approved flag, go back to sleep.
    if not queue_file.exists() or not approved_flag.exists():
        return

    tasks_to_run = []
    with open(queue_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                tasks_to_run.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # ⚡ Consume the flag and wipe the queue immediately so it can't double-fire
    if approved_flag.exists():
        try:
            os.remove(approved_flag)
        except OSError:
            pass

    with open(queue_file, "w", encoding="utf-8") as f:
        f.write("")

    if not tasks_to_run:
        return

    console.print(
        f"\n[bold green]🚀 Found {len(tasks_to_run)} approved tasks. Waking Prefrontal Cortex...[/bold green]"
    )

    # Import PFC locally to avoid circular dependencies during boot
    from System.neuroanatomy.cortical.prefrontal import PrefrontalCortex

    pfc = PrefrontalCortex()

    for idx, task_obj in enumerate(tasks_to_run, 1):
        task_desc = task_obj.get("prompt")
        task_route = task_obj.get("route", "WORKSPACE")
        task_domain = task_obj.get("domain", "GENERAL")

        if task_desc:
            console.print(
                f"[bold blue]--- Processing Approved Queue Item {idx}/{len(tasks_to_run)} ---[/bold blue]"
            )
            try:
                # Execute the task!
                asyncio.run(
                    pfc.execute_goal(task_desc, domain=task_domain, route=task_route)
                )
            except Exception as e:
                console.print(f"[bold red]Queue Task Failed:[/bold red] {str(e)}")

    # Wipe the Obsidian UI clean
    if pending_file.exists():
        with open(pending_file, "w", encoding="utf-8") as f:
            f.write(
                "# 🛑 Pending Swarm Actions\n*No pending actions. The OS is resting.*\n\n"
            )
