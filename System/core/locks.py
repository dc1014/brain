import threading
from collections import defaultdict
from typing import Any


class BiologicalLock:
    """
    Regional Tissue Lock (Granular Mutex).
    Prevents cross-thread collisions on specific files or resources without bottlenecking
    the entire organism. Defaults to a 'global' lock if no resource is specified.
    """

    _locks: dict[str, threading.Lock] = defaultdict(threading.Lock)

    def __init__(self, resource_id: str = "global"):
        self.resource_id = str(resource_id)

    def __enter__(self) -> "BiologicalLock":
        self._lock = self._locks[self.resource_id]
        self._lock.acquire()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._lock.release()
