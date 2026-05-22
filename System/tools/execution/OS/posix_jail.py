import os
import sys


def apply_unix_resource_limits() -> None:
    """Natively enforces strict memory, disk write size, and process ceilings under POSIX systems."""
    if sys.platform != "win32":
        try:
            os.setsid()
        except Exception:
            pass
        try:
            import resource

            # 1. Fork bomb defense: Max 50 simultaneous process threads
            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))

            # 2. RAM ceiling: Max 512MB virtual address space size limit
            mem_limit = 512 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))

            # 3. Disk space isolation: Max 50MB file generation limit
            file_limit = 50 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))

        except Exception:
            pass
