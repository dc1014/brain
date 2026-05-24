# --- System/neuroanatomy/autonomic/vestibular.py ---
import json
import shutil
from pathlib import Path
from System.core.paths import ROOT_DIR, normalize_path
from System.core.file_transaction import atomic_write, read_state_sync

SNAPSHOT_DIR = ROOT_DIR / "System" / "snapshots"
LEDGER_FILE = ROOT_DIR / "System" / "snapshot_ledger.json"


def create_snapshot(directory_path: str | Path) -> None:
    """Creates an isolated backup copy of the target workspace directory prior to tool execution."""
    target = normalize_path(ROOT_DIR / directory_path)
    if not target.exists():
        return

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_target = SNAPSHOT_DIR / target.name

    if snap_target.exists():
        shutil.rmtree(snap_target, ignore_errors=True)

    try:
        shutil.copytree(target, snap_target, dirs_exist_ok=True)
        # Update the workspace state snapshot ledger atomically
        ledger = read_state_sync(LEDGER_FILE, dict)
        ledger[str(target)] = str(snap_target)
        atomic_write(LEDGER_FILE, json.dumps(ledger, indent=2))
    except OSError:
        pass


def commit_transaction() -> None:
    """Purges cached workspace snapshots upon successful step verification."""
    if SNAPSHOT_DIR.exists():
        shutil.rmtree(SNAPSHOT_DIR, ignore_errors=True)
    if LEDGER_FILE.exists():
        LEDGER_FILE.unlink(missing_ok=True)


def restore_balance() -> None:
    """Rolls back the workspace state to the last valid snapshot upon verification failure."""
    ledger = read_state_sync(LEDGER_FILE, dict)
    for original_path_str, snap_path_str in ledger.items():
        original = Path(original_path_str)
        snap = Path(snap_path_str)
        if snap.exists():
            if original.exists():
                shutil.rmtree(original, ignore_errors=True)
            shutil.copytree(snap, original, dirs_exist_ok=True)
    commit_transaction()
