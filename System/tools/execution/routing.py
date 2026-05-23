# --- System/tools/execution/routing.py ---
import os
import sys
import shlex
import stat
import asyncio
from pathlib import Path
from typing import List, Set
from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult

# Pull Rich components for structural command UI assembly
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .validation import parse_and_validate_args


def _render_command_cockpit(
    command: str,
    path_result: str,
    effective_binaries: Set[str],
    created_snapshots: List[str],
    execution_tier: str,
) -> Panel:
    """Renders a comprehensive, high-fidelity terminal user dashboard split into a clean tactical grid layout."""
    layout_grid = Table.grid(padding=(0, 2))
    layout_grid.add_column()
    layout_grid.add_column()

    vector_table = Table.grid(padding=(0, 1))
    vector_table.add_column(style="bold cyan")
    vector_table.add_column(style="white")

    try:
        display_path = Path(path_result).relative_to(ROOT_DIR.resolve())
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

    title_text = Text(
        "🧠 BRAIN OS — SYNAPTIC COMMAND COCKPIT v2.0", style="bold magenta"
    )
    return Panel(master_frame, title=title_text, border_style="magenta", expand=True)


# ⚡ FIX: Gracefully accepts either format and normalizes for downward compatibility
async def execute_command_async(
    command: list[str] | str, directory_path: str, route: str = "UNKNOWN"
) -> ExecutionResult:
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.neuroanatomy.limbic.amygdala import scan_command

    # ⚡ ZERO-DEBT: Normalize to string for legacy text-based scanners to satisfy MyPy
    command_str = command if isinstance(command, str) else shlex.join(command)

    is_safe_path_result, path_result = validate_execution_path(directory_path)
    if not is_safe_path_result:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>",
            block_reason=path_result,
        )

    # Now using command_str so Amygdala string processing doesn't crash
    is_safe_cmd, threat_reason = scan_command(command_str)
    if not is_safe_cmd:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{threat_reason}\n</stderr>\n</shell_output>",
            block_reason=threat_reason,
        )

    parsed_args, effective_binaries, parse_err = parse_and_validate_args(command)
    if parse_err is not None:
        return parse_err

    if parsed_args is None or effective_binaries is None:
        return ExecutionResult(
            success=False,
            output="<shell_output>\n<stderr>\nInternal parsing error.\n</stderr>\n</shell_output>",
            block_reason="Parse Error",
        )

    execution_tier = os.environ.get("BRAIN_EXECUTION_TIER", "0")
    from System.tools.sandbox import REQUIRES_CONTAINMENT, execute_in_sandbox

    if route in REQUIRES_CONTAINMENT:
        return await execute_in_sandbox(
            parsed_args,
            normalize_path(ROOT_DIR / directory_path),
            env_secrets={},
            route=route,
        )

    from .staging import stage_ast_snapshots

    args, created_snapshots, stage_err = stage_ast_snapshots(
        parsed_args, effective_binaries, path_result
    )
    if stage_err is not None:
        return stage_err

    if args is None:
        return ExecutionResult(
            success=False,
            output="<shell_output>\n<stderr>\nStaging failed.\n</stderr>\n</shell_output>",
            block_reason="Staging Error",
        )

    exec_mod = sys.modules["System.tools.execution"]

    try:
        from System.neuroanatomy.autonomic.vestibular import create_snapshot

        create_snapshot(directory_path)

        if os.environ.get("BRAIN_OS_HEADLESS") != "1":
            panel = _render_command_cockpit(
                command_str,
                path_result,
                effective_binaries,
                created_snapshots,
                execution_tier,
            )
            exec_mod.console.print("\n")
            exec_mod.console.print(panel)

            try:
                auth = await asyncio.to_thread(
                    input, "↳ Synaptic Authorization Handle [y/N]: "
                )
                auth = auth.strip().lower()
            except (EOFError, KeyboardInterrupt):
                auth = "n"

            if auth not in ["y", "yes"]:
                exec_mod.console.print(
                    "\n[bold red]❌ TRANSMISSION ABORTED: Security boundary held. Command safely discarded.[/bold red]\n"
                )
                return ExecutionResult(
                    success=False,
                    output="<shell_output>\n<stderr>\nSECURITY BLOCK: User explicitly denied command execution.\n</stderr>\n</shell_output>",
                    block_reason="Denied",
                )
            else:
                exec_mod.console.print(
                    "\n[bold green]⚡ TRANSMISSION AUTHORIZED: Firing synaptic process tree...[/bold green]\n"
                )

        sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=True)
        env_vars = exec_mod._get_scrubbed_env()

        if sys.platform == "win32":
            process = await asyncio.create_subprocess_exec(
                args[0],
                *args[1:],
                cwd=path_result,
                env=env_vars,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                creationflags=0x01000000 | 0x00000200,
            )
        else:
            wrapped_cmd = f"ulimit -v 524288 -u 50 && exec {shlex.join(args)}"
            process = await asyncio.create_subprocess_exec(
                "sh",
                "-c",
                wrapped_cmd,
                cwd=path_result,
                env=env_vars,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

        timeout = 300.0 if "pytest" in command_str else 60.0
        timed_out, full_output = await exec_mod._stream_and_prune_process(
            process, timeout=timeout
        )
        sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=False)

        if timed_out:
            exec_mod._rollback_workspace_transaction(path_result)
            return ExecutionResult(
                success=False,
                output="<shell_output>\n<stderr>\nERROR: Command timed out. Process tree violently pruned.\n</stderr>\n</shell_output>",
                block_reason="Timeout",
            )

        if process.returncode != 0:
            exec_mod._rollback_workspace_transaction(path_result)
            from System.neuroanatomy.systemic.microglia import (
                trigger_immune_response_async,
            )

            healed, heal_msg = await trigger_immune_response_async(
                command_str, full_output, path_result
            )
            if healed:
                return ExecutionResult(
                    success=True,
                    output=f"<shell_output>\n<stdout>\n{heal_msg}\n</stdout>\n</shell_output>",
                )
            else:
                # ⚡ SHIFT-LEFT TOKEN ECONOMICS: Compact failed native output trace blocks
                from System.neuroanatomy.sensory.somatosensory import SensoryTransducer

                compacted_err = SensoryTransducer().compact_terminal_output(
                    parsed_args, full_output
                )
                return ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{compacted_err}\n\nMicroglia Antibody Failed:\\n{heal_msg}\n</stderr>\n</shell_output>",
                    block_reason=f"Failed with exit code {process.returncode}",
                )

        # ⚡ SHIFT-LEFT TOKEN ECONOMICS: Compact successful native command trace blocks
        from System.neuroanatomy.sensory.somatosensory import SensoryTransducer

        compacted_output = SensoryTransducer().compact_terminal_output(
            parsed_args, full_output
        )
        return ExecutionResult(
            success=True,
            output=f"<shell_output>\n<stdout>\n{compacted_output}\n</stdout>\n</shell_output>",
        )
    except Exception as e:
        sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=False)
        sys.modules["System.tools.execution"]._rollback_workspace_transaction(
            path_result
        )
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\nEXECUTION ERROR: {str(e)}\n</stderr>\n</shell_output>",
            block_reason="Crash",
        )
    finally:
        sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=False)
        for snapshot in created_snapshots:
            try:
                if os.path.exists(snapshot):
                    os.chmod(snapshot, stat.S_IWRITE)
                    os.remove(snapshot)
            except Exception:
                pass
