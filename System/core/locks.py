import threading


class BiologicalLock:
    """
    Global OS Mutex (Cellular Membrane Lock).
    Ensures that active Swarm agents, background webhooks, and the file watcher
    do not write to the same memory file at the exact same millisecond.
    """

    _lock = threading.Lock()

    @classmethod
    def acquire(cls):
        cls._lock.acquire()

    @classmethod
    def release(cls):
        cls._lock.release()

    @classmethod
    def __enter__(cls):
        cls.acquire()
        return cls

    @classmethod
    def __exit__(cls, exc_type, exc_val, exc_tb):
        cls.release()
