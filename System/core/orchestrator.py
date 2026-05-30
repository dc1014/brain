import asyncio
import re
import time
from rich.console import Console
from rich.panel import Panel

from System.neuroanatomy.limbic.thalamus import route_sensory_input
from System.core.paths import ROOT_DIR
from System.neuroanatomy.cortical.executive_loop import execute_pipeline

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
    Checks Meta/Pending_Actions.md for approved Swarm instructions.
    Uses lock-free atomic file swapping to read and clear the markdown queue safely.
    """
    pending_file = ROOT_DIR / "Meta" / "Pending_Actions.md"
    completed_file = ROOT_DIR / "Meta" / "Completed_Actions.md"

    if not pending_file.exists() or pending_file.stat().st_size == 0:
        return

    # ⚡ UNIX PHILOSOPHY: Safely pop the queue off the disk in one atomic pass via rename
    temp_file = pending_file.with_suffix(".tmp")
    try:
        pending_file.rename(temp_file)
        pending_file.touch()  # Keep the file visible in Obsidian
    except OSError:
        return  # Collision or file locked

    content = temp_file.read_text(encoding="utf-8")
    temp_file.unlink(missing_ok=True)

    if not content.strip():
        return

    tasks_to_run = []
    blocks = content.split("### ⏳ Pending Task")

    for block in blocks:
        if not block.strip():
            continue

        prompt_match = re.search(r"\*\*Prompt:\*\*\s*(.*?)\n", block)
        route_match = re.search(r"\*\*Thalamus Route:\*\*\s*`(.*?)`", block)
        domain_match = re.search(r"\*\*Domain:\*\*\s*`(.*?)`", block)

        if prompt_match and route_match and domain_match:
            tasks_to_run.append(
                {
                    "prompt": prompt_match.group(1).strip(),
                    "route": route_match.group(1).strip(),
                    "domain": domain_match.group(1).strip(),
                }
            )

    if not tasks_to_run:
        # Revert if parsing failed
        with open(pending_file, "a", encoding="utf-8") as f:
            f.write(content)
        return

    console.print(
        f"\n[bold green]🚀 Found {len(tasks_to_run)} approved tasks in Obsidian ledger. Waking Prefrontal Cortex...[/bold green]"
    )

    # Archive to completed ledger
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    completed_file.parent.mkdir(parents=True, exist_ok=True)
    with open(completed_file, "a", encoding="utf-8") as f:
        f.write(f"\n\n## ✅ Completed Execution Swarm ({timestamp})\n" + content)

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
