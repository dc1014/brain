import json
import shutil
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
VESTIBULAR_DIR = ROOT_DIR / "Meta" / "Vestibular"
LEDGER_PATH = VESTIBULAR_DIR / "ledger.json"


def _get_ledger() -> dict:
    if not LEDGER_PATH.exists():
        return {}
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_ledger(ledger: dict) -> None:
    VESTIBULAR_DIR.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f)


def create_snapshot(filepath: str) -> None:
    """Takes a snapshot of a file before it is modified by an AI tool."""
    target_path = (ROOT_DIR / filepath).resolve()

    # For this iteration, we only protect existing files from being mangled.
    if not target_path.exists() or not target_path.is_file():
        return

    ledger = _get_ledger()
    rel_path = str(target_path.relative_to(ROOT_DIR))

    # If we already snapshotted this file during this execution pipeline, don't overwrite it.
    if rel_path in ledger:
        return

    VESTIBULAR_DIR.mkdir(parents=True, exist_ok=True)
    backup_name = f"{len(ledger)}.bak"
    backup_path = VESTIBULAR_DIR / backup_name

    shutil.copy2(target_path, backup_path)
    ledger[rel_path] = str(backup_path)
    _save_ledger(ledger)

    console.print(
        f"[dim]⚖️  Vestibular: Equilibrium state saved for {target_path.name}[/dim]"
    )


def restore_balance() -> None:
    """Restores all modified files to their original snapshotted state."""
    ledger = _get_ledger()
    if not ledger:
        return

    console.print(
        "\n[bold red]⚖️  Vestibular Reflex Triggered: System lost balance! Restoring file equilibrium...[/bold red]"
    )
    for rel_path, backup_str in ledger.items():
        original_path = ROOT_DIR / rel_path
        backup_path = Path(backup_str)
        if backup_path.exists():
            shutil.copy2(backup_path, original_path)
            console.print(f"[dim]↳ Restored {original_path.name}[/dim]")

    commit_transaction()  # Clear the ledger after restoring


def commit_transaction() -> None:
    """Clears the snapshots because the execution pipeline completed successfully."""
    if VESTIBULAR_DIR.exists():
        shutil.rmtree(VESTIBULAR_DIR)
