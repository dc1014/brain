# --- System/core/concurrency.py ---
import concurrent.futures
import threading
from typing import Optional

_isolated_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None


def _make_thread_daemon() -> None:
    """⚡ Forces spawned worker threads to run as daemons so they never hang process exit."""
    threading.current_thread().daemon = True


def get_isolated_executor(
    max_workers: int = 4,
) -> concurrent.futures.ThreadPoolExecutor:
    """Returns a shared standalone background ThreadPoolExecutor handle."""
    global _isolated_executor
    if _isolated_executor is None:
        _isolated_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="brain_os_worker",
            initializer=_make_thread_daemon,  # Automatically daemonizes every background worker thread
        )
    return _isolated_executor


def lock_concurrency_defaults() -> None:
    """Backwards-compatibility proxy for legacy system CLI initializers."""
    pass
