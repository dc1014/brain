# --- System/neuroanatomy/autonomic/vagus_nerve.py ---
from System.core.paths import ROOT_DIR
from System.core.file_transaction import atomic_write

SIGNAL_FILE = ROOT_DIR / "System" / ".vagus_abort_signal"


def trigger_halt() -> None:
    """Signals the executive loop to abort execution safely via lock-free atomic write."""
    atomic_write(SIGNAL_FILE, "HALT_SIGNAL")


def trigger_recover() -> None:
    """Clears locked memory states and safely removes the abort signal flag."""
    SIGNAL_FILE.unlink(missing_ok=True)
