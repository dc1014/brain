import asyncio
from rich.console import Console
from rich.panel import Panel

from System.neuroanatomy.limbic.thalamus import route_sensory_input
from System.core.paths import ROOT_DIR
from System.neuroanatomy.cortical.executive_loop import execute_pipeline
from System.core.file_transaction import read_and_clear_queue

console = Console()


async def dispatch_task(
    description: str,
    obsidian: bool = False,
    predefined_route: str = "WORKSPACE",
    predefined_domain: str = "GENERAL",
) -> None:
    """
    The Central Routing Hub.
    Intercepts all incoming tasks, passes them through the Thalamus for model/routing
    validation, and triggers the Prefrontal Cortex.
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
        raise ValueError(f"Pulse rejected by pre-flight validation: {reason}")

    final_route = route_type if route_type != "WORKSPACE" else predefined_route
    final_domain = domain if domain != "NONE" else predefined_domain

    console.print(
        f"[bold magenta]🧠 Prefrontal Cortex: Executing task natively...[/bold magenta]\n"
        f"[dim]Goal: {description}\nRoute: {final_route} | Domain: {final_domain}[/dim]"
    )

    await execute_pipeline(description, final_route, final_domain)


async def run_pending_queue() -> None:
    """
    Checks the Meta/queue.jsonl ledger for approved Swarm instructions.
    Uses lock-free atomic file swapping to read and clear the queue safely.
    """
    queue_file = ROOT_DIR / "Meta" / "queue.jsonl"

    # Safely pop the queue off the disk in one atomic pass
    tasks_to_run = read_and_clear_queue(queue_file)

    if not tasks_to_run:
        return

    console.print(
        f"\n[bold green]🚀 Found {len(tasks_to_run)} approved tasks. Waking Prefrontal Cortex...[/bold green]"
    )

    await _process_all_tasks(tasks_to_run)


async def _process_all_tasks(tasks: list[dict]) -> None:
    """Processes all approved queue tasks concurrently within a single event loop."""
    coroutines = []
    for idx, task_obj in enumerate(tasks, 1):
        task_desc = task_obj.get("prompt")
        task_route = task_obj.get("route", "WORKSPACE")
        task_domain = task_obj.get("domain", "GENERAL")

        if task_desc:
            console.print(
                f"[bold blue]--- Processing Approved Queue Item {idx}/{len(tasks)} ---[/bold blue]"
            )
            coroutines.append(
                dispatch_task(
                    task_desc,
                    obsidian=True,
                    predefined_route=task_route,
                    predefined_domain=task_domain,
                )
            )

    results = await asyncio.gather(*coroutines, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            console.print(f"[bold red]Queue Task Failed:[/bold red] {str(res)}")

    pending_file = ROOT_DIR / "Meta" / "Pending_Actions.md"
    if pending_file.exists():
        pending_file.unlink(missing_ok=True)
        console.print("[dim]🧹 Cleared Pending_Actions.md from workspace.[/dim]")
