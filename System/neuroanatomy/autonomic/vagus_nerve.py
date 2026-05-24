import os
from rich.console import Console
from System.core.paths import ROOT_DIR, normalize_path
from System.neuroanatomy.cortical.working_memory import clear_pipeline_state
from System.neuroanatomy.autonomic.vestibular import restore_balance

console = Console()


def trigger_halt() -> None:
    """Vagus Nerve (Parasympathetic): Forces an immediate, safe system-wide halt."""

    # 🔊 THE VERBOSE CHECK
    if os.environ.get("BRAIN_VERBOSE") == "1":
        console.print(
            "[dim magenta][VERBOSE] Vagus Nerve: Polling interrupt signal... Halt triggered![/dim magenta]"
        )

    console.print(
        "[bold red]🚨 VAGUS NERVE ACTIVATED: Initiating Emergency Halt...[/bold red]"
    )

    # 1. Flush the Hippocampus Queue
    clear_pipeline_state()
    console.print(
        "[dim yellow]- Execution queue flushed. No new agents will spawn.[/dim yellow]"
    )

    # 2. Plant the Apoptosis Flag (Tells active prefrontal loops to terminate safely)
    abort_flag = normalize_path(ROOT_DIR / "System" / ".vagus_abort_signal")
    abort_flag.write_text("HALT", encoding="utf-8")
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
