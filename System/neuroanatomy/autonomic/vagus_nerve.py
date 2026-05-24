import os
from rich.console import Console
from System.core.paths import ROOT_DIR, normalize_path
from System.neuroanatomy.autonomic.vestibular import restore_balance
from System.core.file_transaction import write_state_sync_atomic

console = Console()


def trigger_halt() -> None:
    """Vagus Nerve (Parasympathetic): Forces an immediate, safe system-wide halt."""
    if os.environ.get("BRAIN_VERBOSE") == "1":
        console.print(
            "[dim magenta][VERBOSE] Vagus Nerve: Polling interrupt signal... Halt triggered![/dim magenta]"
        )

    console.print(
        "[bold red]🚨 VAGUS NERVE ACTIVATED: Initiating Emergency Halt...[/bold red]"
    )

    # 1. Flush the Hippocampus Queue atomically with zero state corruption risk
    queue_file = ROOT_DIR / "System" / "execution_queue.json"
    write_state_sync_atomic(queue_file, [])
    console.print(
        "[dim yellow]- Execution queue flushed atomically. No new agents will spawn.[/dim yellow]"
    )

    # 2. Plant the Apoptosis Flag atomically
    abort_flag = normalize_path(ROOT_DIR / "System" / ".vagus_abort_signal")
    write_state_sync_atomic(abort_flag, "HALT")

    console.print(
        "[dim yellow]- Abort signal broadcast to all active cortical loops.[/dim yellow]"
    )
    console.print("[bold green]✅ System halted safely.[/bold green]")


def trigger_recover() -> None:
    """Vagus Nerve: Rolls back the file system to the last safe Vestibular snapshot."""
    console.print(
        "[bold yellow]🚨 VAGUS NERVE ACTIVATED: Initiating Vestibular Rollback...[/bold yellow]"
    )

    # 1. Ensure system is halted first to prevent race conditions during rollback
    trigger_halt()

    # 2. Trigger the vestibular rollback
    restore_balance()
    console.print(
        "[bold green]✅ Environment successfully restored from backup.[/bold green]"
    )

    # 3. Clear the abort flag so the OS can boot normally next time
    abort_flag = normalize_path(ROOT_DIR / "System" / ".vagus_abort_signal")
    if abort_flag.exists():
        try:
            os.remove(abort_flag)
        except OSError:
            pass
