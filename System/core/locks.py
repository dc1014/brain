import asyncio
import threading
from pathlib import Path
from typing import Any, Dict
from contextlib import asynccontextmanager, contextmanager
from filelock import FileLock


class BiologicalLock:
    """
    Biological File Lock (IPC + Async) - The Synaptic Cleft.
    Combines robust cross-platform file locking (IPC) with native asyncio/threading locks.
    Prevents both cross-process AND cross-task race conditions on the same memory queues.
    """

    # Class-level dictionaries and a Master Lock to protect them!
    _async_locks: Dict[str, asyncio.Lock] = {}
    _sync_locks: Dict[str, threading.Lock] = {}
    _master_dict_lock = threading.Lock()  # ⚡ THE FIX

    def __init__(self, filepath: str | Path, timeout: float = 15.0):
        self.filepath = Path(filepath).resolve()
        self.lock_path = self.filepath.with_name(f".{self.filepath.name}.lock")
        self.file_lock = FileLock(str(self.lock_path), timeout=timeout)
        self.lock_key = str(self.lock_path)

    @property
    def _local_async(self) -> asyncio.Lock:
        with BiologicalLock._master_dict_lock:  # ⚡ Guarded!
            if self.lock_key not in BiologicalLock._async_locks:
                BiologicalLock._async_locks[self.lock_key] = asyncio.Lock()
            return BiologicalLock._async_locks[self.lock_key]

    @property
    def _local_sync(self) -> threading.Lock:
        with BiologicalLock._master_dict_lock:  # ⚡ Guarded!
            if self.lock_key not in BiologicalLock._sync_locks:
                BiologicalLock._sync_locks[self.lock_key] = threading.Lock()
            return BiologicalLock._sync_locks[self.lock_key]

    # --- LEGACY SUPPORT: `with BiologicalLock():` ---
    def __enter__(self) -> "BiologicalLock":
        self._local_sync.acquire()
        self.file_lock.acquire()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.file_lock.release()
        self._local_sync.release()

    # --- LEGACY SUPPORT: `async with BiologicalLock():` ---
    async def __aenter__(self) -> "BiologicalLock":
        await self._local_async.acquire()
        await asyncio.to_thread(self.file_lock.acquire)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.file_lock.release()
        self._local_async.release()

    # --- NEW SUPPORT (Hippocampus/Tests) ---
    @asynccontextmanager
    async def acquire(self):
        """Asynchronously acquires the local lock, then the IPC lock."""
        async with self._local_async:
            await asyncio.to_thread(self.file_lock.acquire)
            try:
                yield self
            finally:
                self.file_lock.release()

    @contextmanager
    def acquire_sync(self):
        """Synchronously acquires the local lock, then the IPC lock."""
        with self._local_sync:
            self.file_lock.acquire()
            try:
                yield self
            finally:
                self.file_lock.release()
