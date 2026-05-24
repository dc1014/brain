import sys
import multiprocessing
from concurrent.futures import Executor


def lock_concurrency_defaults() -> None:
    """
    🛡️ ZERO-DEBT KERNEL: Enforces identical process architectures across Python versions.
    Python 3.14 changes the default Unix start method to 'forkserver'. We enforce this
    retroactively on 3.12+ to guarantee our data serialization never silently breaks.
    """
    # Windows always uses 'spawn', so we only need to lock the Unix behavior
    if sys.platform != "win32":
        try:
            multiprocessing.set_start_method("forkserver")
        except RuntimeError:
            # This safely catches the error if the context was already set (e.g., during Pytest runs)
            pass


def get_isolated_executor(max_workers: int = 4) -> Executor:
    """
    ⚡ SHIFT-LEFT PERFORMANCE: Dynamically routes parallel workloads.
    On Python 3.14+, leverages PEP 734 Subinterpreters for true multi-core
    thread concurrency. On <3.14, falls back to the rigid ProcessPoolExecutor.
    """
    if sys.version_info >= (3, 14):
        # Python 3.14+ True Multi-Core Threads (Subinterpreters bypassing the GIL)
        from concurrent.futures import InterpreterPoolExecutor  # type: ignore[attr-defined]

        return InterpreterPoolExecutor(max_workers=max_workers)
    else:
        # Python 3.12/3.13 OS-level Process Allocation (Standard Fallback)
        from concurrent.futures import ProcessPoolExecutor

        return ProcessPoolExecutor(max_workers=max_workers)
