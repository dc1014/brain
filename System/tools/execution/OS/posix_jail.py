import os
import sys


def apply_unix_resource_limits() -> None:
    """Limits maximum simultaneous process forks natively under POSIX systems."""
    if sys.platform != "win32":
        try:
            os.setsid()
        except Exception:
            pass
        try:
            import resource

            resource.setrlimit(
                resource.RLIMIT_NPROC, (50, 50)
            )  # Fork bomb protection ceiling
        except Exception:
            pass
