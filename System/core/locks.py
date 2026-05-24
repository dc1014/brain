import asyncio
import threading
from pathlib import Path
from typing import Any, Dict
from contextlib import asynccontextmanager, contextmanager
from filelock import FileLock


class StateLock:
    """
    State File Lock (IPC + Async).
    Combines robust cross-platform file locking (IPC) with native asyncio/threading locks.
    Prevents both cross-process AND cross-task race conditions on the same memory queues.
    """

    _async_locks: Dict[str, asyncio.Lock] = {}
    _sync_locks: Dict[str, threading.Lock] = {}
    _master_dict_lock = threading.Lock()

    def __init__(self, filepath: str | Path, timeout: float = 15.0):
        self.filepath = Path(filepath).resolve()
        self.lock_path = self.filepath.with_name(f".{self.filepath.name}.lock")
        self.file_lock = FileLock(str(self.lock_path), timeout=timeout)
        self.lock_key = str(self.lock_path)

    @property
    def _local_async(self) -> asyncio.Lock:
        with StateLock._master_dict_lock:
            if self.lock_key not in StateLock._async_locks:
                StateLock._async_locks[self.lock_key] = asyncio.Lock()
            return StateLock._async_locks[self.lock_key]

    @property
    def _local_sync(self) -> threading.Lock:
        with StateLock._master_dict_lock:
            if self.lock_key not in StateLock._sync_locks:
                StateLock._sync_locks[self.lock_key] = threading.Lock()
            return StateLock._sync_locks[self.lock_key]

    def __enter__(self) -> "StateLock":
        self._local_sync.acquire()
        self.file_lock.acquire()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.file_lock.release()
        self._local_sync.release()

    async def __aenter__(self) -> "StateLock":
        await self._local_async.acquire()
        self.file_lock.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.file_lock.release()
        self._local_async.release()

    @asynccontextmanager
    async def acquire(self):
        async with self._local_async:
            self.file_lock.acquire()
            try:
                yield self
            finally:
                self.file_lock.release()

    @contextmanager
    def acquire_sync(self):
        with self._local_sync:
            self.file_lock.acquire()
            try:
                yield self
            finally:
                self.file_lock.release()
