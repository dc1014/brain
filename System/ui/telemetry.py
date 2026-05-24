# --- System/ui/telemetry.py ---
import shlex
from pathlib import Path
from typing import List, Set
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def render_command_cockpit(
    command: str,
    path_result: str,
    effective_binaries: Set[str],
    created_snapshots: List[str],
    execution_tier: str,
    root_dir: Path,
) -> Panel:
    """Renders a comprehensive, high-fidelity terminal user dashboard."""
    layout_grid = Table.grid(padding=(0, 2))
    layout_grid.add_column()
    layout_grid.add_column()

    vector_table = Table.grid(padding=(0, 1))
    vector_table.add_column(style="bold cyan")
    vector_table.add_column(style="white")

    try:
        display_path = Path(path_result).relative_to(root_dir.resolve())
    except Exception:
        display_path = Path(path_result)

    vector_table.add_row(
        "Intended Vector : ",
        f"[bold green]{shlex.join(shlex.split(command))}[/bold green]",
    )
    vector_table.add_row("Target Location : ", f"[yellow]📂 {display_path}[/yellow]")
    vector_table.add_row(
        "Active Binary   : ",
        f"[magenta]⚔️ {', '.join(effective_binaries).upper()}[/magenta]",
    )

    firewall_table = Table.grid(padding=(0, 1))
    firewall_table.add_column(style="bold blue")
    firewall_table.add_column(style="dim white")

    tier_desc = "Hardware Sandbox" if execution_tier == "1" else "Native Host Isolated"
    firewall_table.add_row("✓ BBB Guard  :", " Path cleared safety checks.")
    firewall_table.add_row("✓ Amygdala  :", " Heuristic screening passed.")
    firewall_table.add_row("✓ Isolation :", f" Tier {execution_tier} ({tier_desc})")

    layout_grid.add_row(
        Panel(
            vector_table,
            title="[bold cyan]📡 TRANSACTION TELEMETRY[/bold cyan]",
            border_style="cyan",
        ),
        Panel(
            firewall_table,
            title="[bold blue]🛡️ NEURAL FIREWALL PANEL[/bold blue]",
            border_style="blue",
        ),
    )

    staging_table = Table.grid(padding=(0, 1))
    staging_table.add_column(style="bold magenta", width=18)
    staging_table.add_column(style="white")

    if created_snapshots:
        snapshots_tracked = [
            Path(p).name for p in created_snapshots if ".immutable_snapshot_" in p
        ]
        if snapshots_tracked:
            staging_table.add_row(
                "🧬 Atomic Staging :",
                f"[green]Copy-On-Write engaged safely. Generated {len(snapshots_tracked)} snapshot file stubs to prevent TOCTOU race conditions.[/green]",
            )

    staging_table.add_row(
        "🔒 Core Integrity  :",
        "[bold red]Recursive Kernel Protection Mask Activated. Application files set to read-only (IMMUTABLE).[/bold red]",
    )

    master_frame = Table.grid(padding=(0, 0))
    master_frame.add_column()
    master_frame.add_row(
        Text(
            "An autonomous agent is requesting transmission authorization to execute a host terminal process:\n",
            style="italic white",
        )
    )
    master_frame.add_row(layout_grid)
    master_frame.add_row(
        Panel(
            staging_table,
            title="[bold magenta]🧬 COPY-ON-WRITE MEMORY LIFECYCLE[/bold magenta]",
            border_style="magenta",
        )
    )
    master_frame.add_row(
        Text(
            "\nPress [bold green][Y][/bold green] to authorize synaptic transmission, or any other key to discard execution...",
            style="blink yellow",
        )
    )

    return Panel(
        master_frame,
        title=Text("🧠 BRAIN OS — SYNAPTIC COMMAND COCKPIT v2.0", style="bold magenta"),
        border_style="magenta",
        expand=True,
    )
