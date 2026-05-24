import sys
import multiprocessing


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
