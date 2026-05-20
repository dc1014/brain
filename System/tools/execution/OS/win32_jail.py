import sys
import uuid
import ctypes


def apply_windows_job_object(pid: int) -> None:
    """⚡ WIN32 KERNEL MAPPING: Enforces hard resource ceilings on Windows processes."""
    if sys.platform != "win32":
        return

    from ctypes import wintypes

    """
    ⚡ WIN32 KERNEL MAPPING: Enforces hard resource ceilings on Windows processes.
    Binds the child process tree to an isolated Job Object wrapper with OOM and fork-bomb limits.
    """
    if sys.platform != "win32":
        return

    # Win32 Constants
    JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
    JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
            ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.windll.kernel32

    # 1. Instantiate an Ephemeral Job Container
    job_handle = kernel32.CreateJobObjectW(
        None, f"BrainNativeJail-{uuid.uuid4().hex[:8]}"
    )
    if not job_handle:
        return

    # 2. Define Limits: Enforce 50 Max Processes and 512MB hard memory ceiling
    limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    limits.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_ACTIVE_PROCESS
        | JOB_OBJECT_LIMIT_JOB_MEMORY
        | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )
    limits.BasicLimitInformation.ActiveProcessLimit = 50
    limits.JobMemoryLimit = 512 * 1024 * 1024  # 512 MB hard RAM boundary

    # 3. Commit configuration block into the Windows Kernel Scheduler
    sizeof_limits = ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)
    set_info_res = kernel32.SetInformationJobObject(
        job_handle,
        9,  # JobObjectExtendedLimitInformation
        ctypes.byref(limits),
        sizeof_limits,
    )

    if set_info_res:
        # 4. Open process access token handle and bind it physically to the resource pool
        PROCESS_SET_QUOTA = 0x0100
        PROCESS_TERMINATE = 0x0001
        proc_handle = kernel32.OpenProcess(
            PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid
        )
        if proc_handle:
            kernel32.AssignProcessToJobObject(job_handle, proc_handle)
            kernel32.CloseHandle(proc_handle)

    if not hasattr(sys, "_brain_active_jobs"):
        setattr(sys, "_brain_active_jobs", [])

    active_jobs = getattr(sys, "_brain_active_jobs")
    if isinstance(active_jobs, list):
        active_jobs.append(job_handle)
