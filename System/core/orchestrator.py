import asyncio
import json
import os
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
import yaml  # type: ignore

from System.core.paths import ROOT_DIR
from System.llm import log_interaction
from System.runtime import analyze_task, execute_pipeline

console = Console()

# --- SHIFT-LEFT: Load config safely for the Orchestrator ---
CONFIG_DIR = ROOT_DIR / "System" / "config"
try:
    AGENT_CONFIG = {}
    for filename in ["models.yaml", "agents.yaml", "routes.yaml"]:
        with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
            AGENT_CONFIG.update(yaml.safe_load(f))
except Exception as e:
    console.print(f"[bold red]Fatal Error loading config:[/bold red] {e}")
    AGENT_CONFIG = {"models": {"gpt_mini": "openai/gpt-4o-mini"}, "routes": {}}


async def dispatch_task(description: str, obsidian: bool = False) -> None:
    """Prefrontal Cortex: Handles pre-flight routing, domain context, and execution authorization."""
    with console.status(
        "[bold yellow]🛡️ Dispatcher is analyzing the task...[/bold yellow]",
        spinner="dots",
    ):
        is_valid, reason, route_type, domain, dispatch_usage = await analyze_task(
            description
        )

    if not is_valid:
        console.print(
            Panel(f"[bold red]Task Rejected:[/bold red] {reason}", border_style="red")
        )
        await log_interaction(
            "Dispatcher",
            AGENT_CONFIG["models"]["gpt_mini"],
            "Dispatcher Logic",
            description,
            f"REJECTED: {reason}",
            dispatch_usage,
            "REJECTED",
            "NONE",
        )
        return

    console.print(
        f"[dim]✅ Pre-Flight Passed. Assigned Route: [bold]{route_type}[/bold] | Domain Context: [bold cyan]{domain}[/bold cyan][/dim]"
    )

    # --- THE HANDOFF PROTOCOL (OBSIDIAN UI) ---
    if obsidian:
        queue_file = ROOT_DIR / "System" / "queue.jsonl"
        pending_file = ROOT_DIR / "System" / "Pending_Actions.md"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. Deterministic Machine Queue
        queue_data = {
            "timestamp": timestamp,
            "route": route_type,
            "domain": domain,
            "prompt": description,
        }
        with open(queue_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(queue_data) + "\n")

        # 2. Human-Readable Glass Pane
        ticket = (
            f"\n### ⏳ Pending Task: {route_type}\n"
            f"**Logged:** {timestamp} | **Domain:** `{domain}`\n"
            f"**Prompt:** {description}\n"
            f"- [ ] **Status:** PENDING EXECUTION\n"
            f"---\n"
        )
        with open(pending_file, "a", encoding="utf-8") as f:
            f.write(ticket)

        console.print(
            "[bold green]✅ Task safely queued in System/queue.jsonl[/bold green]"
        )
        return

    # --- STANDARD TERMINAL EXECUTION ---
    pipeline = list(AGENT_CONFIG["routes"].get(route_type, []))
    agents_to_run = []
    for step in pipeline:
        if "agent" in step:
            agents_to_run.append(step["agent"])
        elif "swarm" in step:
            swarm_agents = [s["agent"] for s in step["swarm"]]
            agents_to_run.append(f"[Parallel Swarm: {', '.join(swarm_agents)}]")

    console.print("\n[bold yellow]⚠️  PIPELINE AUTHORIZATION[/bold yellow]")
    console.print(
        f"This task requires the [bold]{route_type}[/bold] route, which will wake up:"
    )
    console.print(f"[bold cyan]{' -> '.join(agents_to_run)}[/bold cyan]")

    try:
        auth = (
            input("\nAuthorize AI execution and token spend? [y/N]: ").strip().lower()
        )
    except (EOFError, KeyboardInterrupt):
        auth = "n"

    if auth not in ["y", "yes"]:
        console.print(
            "\n[bold red]🛑 Task Aborted: User declined pipeline execution.[/bold red]\n"
        )
        return

    await execute_pipeline(description, route_type, domain)


def run_pending_queue() -> None:
    """Reads the deterministic queue.jsonl, executes all tasks sequentially, and clears the queue."""
    os.environ["BRAIN_OS_HEADLESS"] = "1"

    queue_file = ROOT_DIR / "System" / "queue.jsonl"
    pending_file = ROOT_DIR / "System" / "Pending_Actions.md"

    if not queue_file.exists() or queue_file.stat().st_size == 0:
        console.print("[yellow]No pending tasks found in queue.jsonl.[/yellow]")
        return

    tasks_to_run = []
    with open(queue_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                tasks_to_run.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not tasks_to_run:
        console.print("[red]Could not parse any valid tasks from the queue.[/red]")
        return

    console.print(
        f"[bold green]🚀 Found {len(tasks_to_run)} pending tasks. Executing sequence...[/bold green]"
    )

    for idx, task_obj in enumerate(tasks_to_run, 1):
        console.print(
            f"\n[bold blue]--- Executing Task {idx}/{len(tasks_to_run)} ---[/bold blue]"
        )
        task_desc = task_obj.get("prompt")
        if not task_desc:
            continue

        # Re-analyze to ensure context is perfectly fresh before execution
        is_valid, reason, route_type, domain, _ = asyncio.run(analyze_task(task_desc))
        if is_valid:
            asyncio.run(execute_pipeline(task_desc, route_type, domain))
        else:
            console.print(
                f"[bold red]Task failed pre-flight validation:[/bold red] {reason}"
            )

    # THE WIPE
    queue_file.write_text("", encoding="utf-8")
    if pending_file.exists():
        pending_file.write_text(
            "# ⚠️ Pending Execution Queue\n\n*Queue is currently empty.*\n",
            encoding="utf-8",
        )
    console.print(
        "\n[bold green]✅ Queue executed and cleared successfully![/bold green]"
    )
