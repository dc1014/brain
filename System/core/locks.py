import os
import time
import asyncio
import threading
from typing import Any, Dict
from rich.console import Console

console = Console()


class BiologicalLock:
    """
    Hardened Hybrid Biological Lock (Dual Protocol).
    Provides BOTH async (`async with`) and sync (`with`) context managers.
    Combines memory fencing with thread-isolated filesystem locks.
    """

    _local_async_locks: Dict[str, asyncio.Lock] = {}
    _local_sync_locks: Dict[str, threading.Lock] = {}

    def __init__(self, lock_file_path: str, timeout: float = 10.0) -> None:
        self.lock_file: str = f"{lock_file_path}.lock"
        self.timeout: float = timeout

        # Async memory lock (for asyncio loop safety)
        if self.lock_file not in self._local_async_locks:
            self._local_async_locks[self.lock_file] = asyncio.Lock()
        self.local_async_lock: asyncio.Lock = self._local_async_locks[self.lock_file]

        # Sync memory lock (for native thread safety)
        if self.lock_file not in self._local_sync_locks:
            self._local_sync_locks[self.lock_file] = threading.Lock()
        self.local_sync_lock: threading.Lock = self._local_sync_locks[self.lock_file]

    def _try_acquire_file_lock(self) -> bool:
        """Synchronous file IO for cross-process locking using Atomic OS operations."""
        try:
            # ⚡ ZERO-DEBT: os.O_CREAT | os.O_EXCL ensures atomic creation.
            # This completely eliminates TOCTOU (Time-Of-Check-To-Time-Of-Use) race conditions.
            fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
            return True
        except (FileExistsError, OSError):
            return False

    def _release_file_lock(self) -> None:
        """Synchronous file removal."""
        if os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
            except OSError:
                pass

    # --- ASYNC CONTEXT MANAGER (The Myelinated Fast-Path) ---
    async def __aenter__(self) -> "BiologicalLock":
        await self.local_async_lock.acquire()
        start_time = time.time()
        while True:
            success = await asyncio.to_thread(self._try_acquire_file_lock)
            if success:
                return self

            if time.time() - start_time > self.timeout:
                self.local_async_lock.release()
                raise TimeoutError(
                    f"Synaptic Lock Timeout: Could not secure {self.lock_file}"
                )

            await asyncio.sleep(0.05)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await asyncio.to_thread(self._release_file_lock)
        self.local_async_lock.release()

    # --- SYNC CONTEXT MANAGER (Legacy / Somatic Compatibility) ---
    def __enter__(self) -> "BiologicalLock":
        self.local_sync_lock.acquire()
        start_time = time.time()
        while True:
            if self._try_acquire_file_lock():
                return self

            if time.time() - start_time > self.timeout:
                self.local_sync_lock.release()
                raise TimeoutError(
                    f"Synaptic Lock Timeout: Could not secure {self.lock_file}"
                )

            time.sleep(0.05)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._release_file_lock()
        self.local_sync_lock.release()
