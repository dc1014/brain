# --- System/core/concurrency.py ---
import concurrent.futures
from typing import Optional

_isolated_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None


def get_isolated_executor(
    max_workers: int = 4,
) -> concurrent.futures.ThreadPoolExecutor:
    """Returns a shared standalone background ThreadPoolExecutor handle."""
    global _isolated_executor
    if _isolated_executor is None:
        _isolated_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="brain_os_worker",
            # removed the incompatible Python 3.12 initializer
        )
    return _isolated_executor


def lock_concurrency_defaults() -> None:
    """Backwards-compatibility proxy for legacy system CLI initializers."""
    pass
