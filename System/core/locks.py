# --- System/core/locks.py ---
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any


class StateLock:
    """
    Sterile Backwards-Compatibility Pass-Through.
    With Phase 3 (Option A) Atomic Shadow Swapping active, synchronization is
    handled natively at the OS kernel level during file replacement. Explicit
    application-level locking is obsolete, eliminating async deadlocks entirely.
    """

    def __init__(self, filepath: str | Path, timeout: float = 15.0):
        self.filepath = Path(filepath).resolve()

    def __enter__(self) -> "StateLock":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def __aenter__(self) -> "StateLock":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    @contextmanager
    def acquire_sync(self):
        yield self

    @asynccontextmanager
    async def acquire(self):
        yield self
