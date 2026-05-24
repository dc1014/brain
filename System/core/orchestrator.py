import asyncio
import json
import os
from filelock import FileLock
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
        # ⚡ Thalamic routing intercepts the prompt and mutates configurations dynamically
        is_valid, reason, route_type, domain, _ = await route_sensory_input(description)

    if not is_valid:
        console.print(
            Panel(f"[bold red]Pulse Rejected:[/bold red] {reason}", border_style="red")
        )
        raise ValueError(f"Pulse rejected by pre-flight validation: {reason}")

    # If the Thalamus returned a default, respect the user's hardcoded CLI inputs if provided
    final_route = route_type if route_type != "WORKSPACE" else predefined_route
    final_domain = domain if domain != "GENERAL" else predefined_domain

    # ⚡ THE FIX: Identify background queue tasks as AUTONOMIC so they don't wake the sleep cycle
    target_origin = "AUTONOMIC" if obsidian else "HUMAN"

    await execute_pipeline(description, final_route, final_domain, origin=target_origin)


def run_pending_queue() -> None:
    """
    Cognitive Queue Processor:
    Reads pending tasks, checks for dopamine release flags, and executes them
    through the secure Thalamic routing pipeline.
    """
    queue_file = ROOT_DIR / "Meta" / "queue.jsonl"
    pending_file = ROOT_DIR / "Meta" / "Pending_Actions.md"
    approved_flag = ROOT_DIR / "Meta" / ".approved"
    lock_file = ROOT_DIR / "Meta" / "queue.lock"  # ⚡ ZERO-DEBT: State lock

    # Fast-fail check before waiting for locks
    if not queue_file.exists() or not approved_flag.exists():
        return

    tasks_to_run = []

    # ⚡ ZERO-DEBT: Wrap the state mutations in a strict thread-safe file lock
    # This completely eliminates TOCTOU (Time-Of-Check to Time-Of-Use) race conditions
    with FileLock(str(lock_file), timeout=5):
        # Double-check inside the lock to ensure another thread didn't steal it
        if not queue_file.exists() or not approved_flag.exists():
            return

        with open(queue_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    tasks_to_run.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # Consume the flag and wipe the queue atomically so it can't double-fire
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

    for idx, task_obj in enumerate(tasks_to_run, 1):
        task_desc = task_obj.get("prompt")
        task_route = task_obj.get("route", "WORKSPACE")
        task_domain = task_obj.get("domain", "GENERAL")

        if task_desc:
            console.print(
                f"[bold blue]--- Processing Approved Queue Item {idx}/{len(tasks_to_run)} ---[/bold blue]"
            )
            try:
                # ⚡ THE FIX: Route the queue task through the Thalamus instead of skipping straight to the PFC
                asyncio.run(
                    dispatch_task(
                        task_desc,
                        obsidian=True,
                        predefined_route=task_route,
                        predefined_domain=task_domain,
                    )
                )
            except Exception as e:
                console.print(f"[bold red]Queue Task Failed:[/bold red] {str(e)}")

    # Wipe the Obsidian UI clean
    if pending_file.exists():
        with open(pending_file, "w", encoding="utf-8") as f:
            f.write(
                "# 🛑 Pending Swarm Actions\n*No pending actions. The OS is resting.*\n\n"
            )
