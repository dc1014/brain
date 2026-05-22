import os
import sys
import shutil
import asyncio
from pathlib import Path
from typing import Optional, List
from System.core.paths import ROOT_DIR  # ⚡ NEW: Import the project root path

_PRE_WARMED_WORKER: Optional[asyncio.subprocess.Process] = None
_WARMING_TASK: Optional[asyncio.Task] = None
_ALL_SPAWNED_PROCESSES: List[asyncio.subprocess.Process] = []


async def _spawn_worker(workspace_path: Path) -> asyncio.subprocess.Process:
    """🛡️ THE ABSOLUTE VAULT: Spawns a cryptographically isolated WebAssembly execution cell."""
    deno_path = shutil.which("deno")

    if not deno_path:
        raise RuntimeError(
            "CRITICAL SECURITY BLOCK: Deno runtime not found. Refusing to execute untrusted code natively."
        )

    safe_env = os.environ.copy()
    safe_env["NO_COLOR"] = "1"

    # ⚡ FIXED: Create a persistent Deno cache in the project root so tests
    # don't re-download Pyodide every run! This stops the "hanging".
    deno_cache_dir = ROOT_DIR / ".deno_cache"
    deno_cache_dir.mkdir(exist_ok=True)
    safe_env["DENO_DIR"] = str(deno_cache_dir.resolve())

    proc = await asyncio.create_subprocess_exec(
        deno_path,
        "run",
        "--quiet",
        "--no-prompt",
        "--no-config",
        "--no-lock",
        "--v8-flags=--max-old-space-size=256,--wasm-max-mem-pages=4096",
        "--allow-net",
        "--allow-import",
        # ⚡ Whitelist the shared cache folder alongside the workspace
        f"--allow-read={workspace_path.resolve()},{deno_cache_dir.resolve()}",
        f"--allow-write={workspace_path.resolve()},{deno_cache_dir.resolve()}",
        "-",
        env=safe_env,
        cwd=str(workspace_path.resolve()),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
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
