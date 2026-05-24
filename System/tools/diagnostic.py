import os
import json
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from System.core.paths import ROOT_DIR

console = Console()


def get_system_vitals() -> Panel:
    """
    INTEROCEPTION: Compiles real-time structural, immune, and metabolic vitals
    of Brain OS into an absolute-zero debt telemetry report.
    """
    # 🛡️ 1. Evaluate Membrane Integrity
    bbb_headless = os.environ.get("BRAIN_OS_HEADLESS") == "1"
    membrane_status = (
        "[bold yellow]REM Sleep Mode (Headless)[/bold yellow]"
        if bbb_headless
        else "[bold green]Awake (HITL Guard Active)[/bold green]"
    )

    # Check if FTS5 Database exists
    db_path = ROOT_DIR / "System" / "config" / "hippocampus.db"
    db_status = (
        "[green]Healthy (FTS5 Indexed)[/green]"
        if db_path.exists()
        else "[yellow]Unindexed (Rebuild Pending)[/yellow]"
    )

    # 🦠 2. Gather Immune/Microglia Interventions
    log_file = ROOT_DIR / "logs" / "agent_interactions.jsonl"
    immune_heal_count = 0
    total_tokens_burned = 0
    total_interactions = 0

    if log_file.is_file():
        try:
            lines = log_file.read_text(encoding="utf-8").splitlines()
            total_interactions = len(lines)
            for line in lines:
                try:
                    data = json.loads(line)
                    # Check for Microglia success flags or keyword markers
                    response_text = data.get("response", "")
                    if (
                        "Microglia autonomously applied a patch" in response_text
                        or "Microglia Successfully Healed" in response_text
                    ):
                        immune_heal_count += 1

                    # Track metabolic loads
                    tokens = data.get("tokens", {})
                    total_tokens_burned += tokens.get("total_tokens", 0)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

    # 🧠 3. Count Consolidated Engrams
    engram_dir = ROOT_DIR / "Meta" / "Engrams"
    engram_count = 0
    if engram_dir.exists():
        engram_count = len(list(engram_dir.glob("*.json")))

    # 📊 4. Assemble Telemetry Table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Vital Sign", style="cyan")
    table.add_column("Current Measurement", style="white")

    table.add_row("Circadian Rhythm Status", membrane_status)
    table.add_row("Hippocampus Core (FTS5)", db_status)
    table.add_row("Consolidated Muscle Memories", f"{engram_count} active Engrams")
    table.add_row(
        "Immune System Interventions",
        f"{immune_heal_count} successful cellular healings",
    )
    table.add_row("Active Ledger Volume", f"{total_interactions} recorded synapses")
    table.add_row(
        "Current Metabolic Cost", f"{total_tokens_burned:,} tokens burned this cycle"
    )

    return Panel(
        table,
        title="[bold magenta]📊 Brain OS: Autonomic Telemetry Dashboard[/bold magenta]",
        border_style="magenta",
        expand=False,
    )


def render_pipeline_diagnostics(session_metabolism: dict, eval_retries: int) -> None:
    """Renders the terminal UI for token metabolism tracking."""
    diag_table = Table(show_header=True, header_style="bold magenta", box=None)
    diag_table.add_column("Engine / Model")
    diag_table.add_column("Input (Prompt)", justify="right")
    diag_table.add_column("Output (Comp)", justify="right")
    diag_table.add_column("Sum", justify="right", style="bold cyan")

    grand_prompt = 0
    grand_comp = 0

    for m_id, counts in session_metabolism.items():
        p = counts["prompt"]
        c = counts["comp"]
        total = p + c
        grand_prompt += p
        grand_comp += c
        diag_table.add_row(m_id, f"{p:,}", f"{c:,}", f"{total:,}")

    diag_table.add_row("", "", "", "")
    diag_table.add_row(
        "[bold]TOTAL METABOLISM[/bold]",
        f"[bold]{grand_prompt:,}[/bold]",
        f"[bold]{grand_comp:,}[/bold]",
        f"[bold]{grand_prompt + grand_comp:,}[/bold]",
    )

    console.print(
        Panel(
            diag_table,
            title=f"📊 [ PIPELINE DIAGNOSTICS | Loops: {eval_retries} ] 📊",
            border_style="blue",
        )
    )
