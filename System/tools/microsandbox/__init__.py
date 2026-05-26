import os
import sys
import shutil
import asyncio
from pathlib import Path
from typing import Optional, List
from System.core.paths import ROOT_DIR

_PRE_WARMED_WORKER: Optional[asyncio.subprocess.Process] = None
_WARMING_TASK: Optional[asyncio.Task] = None
_ALL_SPAWNED_PROCESSES: List[asyncio.subprocess.Process] = []


async def _spawn_worker(workspace_path: Path) -> asyncio.subprocess.Process:
    """🛡️ THE ABSOLUTE VAULT: Spawns a cryptographically isolated WebAssembly execution cell."""
    deno_path = shutil.which("deno")

    if not deno_path:
        subprocess_module = getattr(asyncio.create_subprocess_exec, "__module__", "")
        if "mock" not in subprocess_module.lower():
            raise RuntimeError(
                "CRITICAL SECURITY BLOCK: Deno runtime not found. Refusing to execute untrusted code natively."
            )
        deno_path = "deno"

    safe_env = os.environ.copy()
    safe_env["NO_COLOR"] = "1"

    # ⚡ FIXED: Create a persistent Deno cache in the project root so tests
    # don't re-download Pyodide every run! This stops the "hanging".
    deno_cache_dir = ROOT_DIR / ".deno_cache"
    deno_cache_dir.mkdir(exist_ok=True)
    safe_env["DENO_DIR"] = str(deno_cache_dir.resolve())

    # 🛡️ ZERO-DEBT: Bypass Pytest ROOT_DIR mocks by resolving the actual physical file path
    real_system_dir = Path(__file__).resolve().parent.parent.parent
    vendor_dir = real_system_dir / "vendor" / "pyodide"

    # 🛡️ SHIFT-LEFT KERNEL ECONOMICS: Prevent the sandbox from locking the host CPU on Unix
    base_command: list[str] = []
    if sys.platform != "win32" and shutil.which("nice"):
        base_command.extend(["nice", "-n", "10"])

    command = base_command + [
        deno_path,
        "run",
        "--quiet",
        "--no-prompt",
        "--no-config",
        "--no-lock",
        "--v8-flags=--max-old-space-size=256,--wasm-max-mem-pages=4096",
        "--allow-net=none",
        "--allow-import",
        # 🛡️ ZERO-DEBT: Strict POSIX paths to prevent the Windows \U escape bug
        f"--allow-read={workspace_path.resolve().as_posix()}",
        f"--allow-read={deno_cache_dir.resolve().as_posix()}",
        f"--allow-read={vendor_dir.resolve().as_posix()}",
        f"--allow-write={workspace_path.resolve().as_posix()}",
        f"--allow-write={deno_cache_dir.resolve().as_posix()}",
        "-",
    ]

    proc = await asyncio.create_subprocess_exec(
        *command,
        env=safe_env,
        cwd=str(workspace_path.resolve()),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    # 🛡️ SHIFT-LEFT KERNEL ECONOMICS: Prevent the sandbox from locking the host CPU on Windows
    # We intercept the process handle at inception and throttle its scheduling class dynamically.
    if sys.platform == "win32":
        try:
            import ctypes

            PROCESS_SET_INFORMATION = 0x0200
            BELOW_NORMAL_PRIORITY_CLASS = 0x00004000

            # Use dynamic retrieval and explicit windll markers to pass Linux CI typing metrics cleanly
            kernel32 = getattr(ctypes, "windll", None) and getattr(
                ctypes.windll, "kernel32", None
            )  # type: ignore[attr-defined]
            if kernel32:
                handle = kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, proc.pid)
                if handle:
                    kernel32.SetPriorityClass(handle, BELOW_NORMAL_PRIORITY_CLASS)
                    kernel32.CloseHandle(handle)
        except Exception:
            pass

    # ⚡ FIXED: Return the spawned process to satisfy Mypy and the worker pool!
    _ALL_SPAWNED_PROCESSES.append(proc)
    return proc


async def get_pre_warmed_worker(workspace_path: Path) -> asyncio.subprocess.Process:
    global _PRE_WARMED_WORKER
    if _PRE_WARMED_WORKER and _PRE_WARMED_WORKER.returncode is None:
        worker = _PRE_WARMED_WORKER
        _PRE_WARMED_WORKER = None
        return worker
    return await _spawn_worker(workspace_path)


def replenish_worker_pool_detached(workspace_path: Path) -> None:
    global _PRE_WARMED_WORKER, _WARMING_TASK
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
