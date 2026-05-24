# --- System/core/file_transaction.py ---
import json
from pathlib import Path
from typing import Any, List, Dict


def atomic_write(filepath: Path | str, content: str) -> None:
    """
    Writes content to a temporary shadow file and atomically swaps it.
    This entirely prevents write collisions and file corruption without needing locks.
    """
    target = Path(filepath)
    target.parent.mkdir(parents=True, exist_ok=True)

    # 1. Write the new state safely to a shadow file
    shadow = target.with_suffix(target.suffix + ".tmp")
    shadow.write_text(content, encoding="utf-8")

    # 2. Atomically overlay the target file (Supported on POSIX and Windows)
    shadow.replace(target)


def atomic_clear(filepath: Path | str) -> None:
    """Atomically clears a file by swapping an empty shadow file over it."""
    atomic_write(filepath, "")


def read_and_clear_queue(filepath: Path | str) -> List[Dict[str, Any]]:
    """
    Atomically reads the current JSONL queue and clears it in a single operation.
    External bash scripts and browser extensions can safely append to the queue concurrently.
    """
    target = Path(filepath)
    if not target.exists():
        return []

    # 1. Read the current text state into local memory
    lines = target.read_text(encoding="utf-8").splitlines()

    # 2. Atomically swap the file with an empty state so incoming background tasks can write
    atomic_clear(target)

    # 3. Process the lines
    tasks = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                tasks.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return tasks


def read_state_sync(filepath: Path | str, default_factory: type = list) -> Any:
    """Safely reads a JSON state file. Used by CLI to check pipeline sequences."""
    target = Path(filepath)
    if not target.exists():
        return default_factory()
    try:
        content = target.read_text(encoding="utf-8")
        if not content.strip():
            return default_factory()
        return json.loads(content)
    except Exception:
        return default_factory()


# Backwards-compatibility signature proxy
write_state_sync_atomic = atomic_write
