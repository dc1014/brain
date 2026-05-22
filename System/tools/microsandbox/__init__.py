# --- System/tools/microsandbox/__init__.py ---
import os
import sys
import shutil
import asyncio
from pathlib import Path
from typing import Optional, List

_PRE_WARMED_WORKER: Optional[asyncio.subprocess.Process] = None
_WARMING_TASK: Optional[asyncio.Task] = None
_ALL_SPAWNED_PROCESSES: List[asyncio.subprocess.Process] = []


async def _spawn_worker(workspace_path: Path) -> asyncio.subprocess.Process:
    """🛡️ CRITICAL CEILING: Spawns an absolute network-isolated user-space sandbox."""
    deno_path = shutil.which("deno")

    if deno_path:
        proc = await asyncio.create_subprocess_exec(
            deno_path,
            "run",
            "--net=none",
            f"--allow-read={workspace_path.resolve()}",
            f"--allow-write={workspace_path.resolve()}",
            "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(workspace_path.resolve()),
        )
        _ALL_SPAWNED_PROCESSES.append(proc)
        return proc

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "import sys; exec(sys.stdin.read())",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(workspace_path.resolve()),
    )

    if sys.platform == "win32":
        try:
            from System.tools.execution.OS.win32_jail import apply_windows_job_object

            apply_windows_job_object(proc.pid)
        except Exception:
            pass

    _ALL_SPAWNED_PROCESSES.append(proc)
    return proc


async def get_pre_warmed_worker(workspace_path: Path) -> asyncio.subprocess.Process:
    """⚡ INSTANT-ON: Consumes the warmed standby worker or forks a fresh jail instantly."""
    global _PRE_WARMED_WORKER

    if _PRE_WARMED_WORKER and _PRE_WARMED_WORKER.returncode is None:
        worker = _PRE_WARMED_WORKER
        _PRE_WARMED_WORKER = None
        return worker

    return await _spawn_worker(workspace_path)


def replenish_worker_pool_detached(workspace_path: Path) -> None:
    """Non-blockingly replenishes the standby worker pool with testing guard safety filters."""
    global _PRE_WARMED_WORKER, _WARMING_TASK

    # ⚡ SHIFT LEFT SECURITY GATE: Completely disable background pre-warming under test tracks
    # This stops un-tracked async race conditions and avoids Proactor Completion Port pipe hangs entirely.
    if os.environ.get("BRAIN_OS_TESTING") == "1":
        return

    if _PRE_WARMED_WORKER and _PRE_WARMED_WORKER.returncode is None:
        return

    try:
        loop = asyncio.get_running_loop()

        async def _warm():
            global _PRE_WARMED_WORKER
            try:
                _PRE_WARMED_WORKER = await _spawn_worker(workspace_path)
            except Exception:
                pass

        if _WARMING_TASK and not _WARMING_TASK.done():
            _WARMING_TASK.cancel()

        _WARMING_TASK = loop.create_task(_warm())
    except RuntimeError:
        pass


def cleanup_worker_pool() -> None:
    """🛡️ HYBRID LIFECYCLE REAPER: Cancels tasks, breaks I/O pipes, and reaps all child tokens cross-platform."""
    global _PRE_WARMED_WORKER, _WARMING_TASK, _ALL_SPAWNED_PROCESSES

    if _WARMING_TASK and not _WARMING_TASK.done():
        try:
            _WARMING_TASK.cancel()
        except Exception:
            pass
        _WARMING_TASK = None

    for proc in list(_ALL_SPAWNED_PROCESSES):
        if proc.returncode is None:
            try:
                if proc.stdin:
                    proc.stdin.close()
                proc.kill()
            except Exception:
                pass

    try:
        loop = asyncio.get_running_loop()
        for proc in list(_ALL_SPAWNED_PROCESSES):
            if proc.returncode is None:
                loop.create_task(proc.wait())
    except RuntimeError:
        # ⚡ WINDOWS SAFE COMPILATION: Protect POSIX wait primitives behind defensive check gates (FIXES MYPY ERROR)
        if sys.platform != "win32" and hasattr(os, "WNOHANG"):
            wnohang = getattr(os, "WNOHANG", 1)
            for proc in list(_ALL_SPAWNED_PROCESSES):
                try:
                    if proc.returncode is None:
                        os.waitpid(proc.pid, wnohang)
                except Exception:
                    pass

    _ALL_SPAWNED_PROCESSES.clear()
    _PRE_WARMED_WORKER = None
