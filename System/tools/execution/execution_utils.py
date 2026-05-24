import os
import sys
import stat
import asyncio
import signal
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple
from rich.console import Console

from System.core.paths import ROOT_DIR

console = Console()
MAX_OUTPUT_CHUNKS = 2000
CHUNK_SIZE = 4096


def set_system_volume_mask(read_only: bool) -> None:
    """🛡️ VOLUME MASKING: Toggles strict kernel-level file protections."""
    try:
        system_core_dir = Path(ROOT_DIR / "System").resolve()
        if not system_core_dir.exists():
            return
        for item in system_core_dir.rglob("*"):
            try:
                rel_path_str = str(item.relative_to(system_core_dir))
            except ValueError:
                rel_path_str = str(item)
            if (
                "Temp" in rel_path_str
                or "pytest-" in rel_path_str
                or "apoptosis" in rel_path_str
            ):
                continue
            if item.is_file():
                try:
                    current_mode = os.stat(item).st_mode
                    if read_only:
                        os.chmod(
                            item,
                            current_mode
                            & ~stat.S_IWRITE
                            & ~stat.S_IWGRP
                            & ~stat.S_IWOTH,
                        )
                    else:
                        os.chmod(item, current_mode | stat.S_IWRITE)
                except Exception:
                    pass
    except Exception:
        pass


def get_scrubbed_env() -> Dict[str, str]:
    safe_env: Dict[str, str] = {}
    allowlist = {
        "PATH",
        "SYSTEMROOT",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "HOME",
        "USER",
        "SHELL",
        "TERM",
        "LANG",
        "TMP",
        "TEMP",
        "VIRTUAL_ENV",
        "UV_PYTHON",
        "UV_PROJECT_ENVIRONMENT",
    }
    for k, v in os.environ.items():
        if k.upper() in allowlist:
            safe_env[k] = v
    return safe_env


def rollback_workspace_transaction(path_result: str) -> None:
    """⚡ TRANSACTION RECOVERY: Automatically purges modifications on execution failure."""
    try:
        target_dir = Path(path_result).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            return
        for item in list(target_dir.rglob("*")):
            try:
                if item.is_file() and (
                    ".immutable_snapshot_" in item.name
                    or ".wrapped_" in item.name
                    or "apoptosis_membrane" in item.name
                ):
                    os.chmod(str(item), stat.S_IWRITE)
                    os.remove(str(item))
            except Exception:
                pass
    except Exception:
        pass


def get_subprocess_kwargs() -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    return kwargs


async def stream_and_prune_process(
    process: asyncio.subprocess.Process, timeout: float
) -> Tuple[bool, str]:
    async def _stream() -> str:
        output_chunks, chunk_count = [], 0
        if process.stdout:
            while True:
                chunk = await process.stdout.read(CHUNK_SIZE)
                if not chunk:
                    break
                decoded_chunk = chunk.decode(errors="replace")
                console.print(decoded_chunk, end="")
                output_chunks.append(decoded_chunk)
                chunk_count += 1
                if chunk_count > MAX_OUTPUT_CHUNKS:
                    output_chunks.append(
                        "\nSECURITY BLOCK: Execution halted due to excessive output"
                    )
                    try:
                        if sys.platform == "win32":
                            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                        else:
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except Exception:
                        process.kill()
                    break
        await process.wait()
        return "".join(output_chunks)

    try:
        return False, await asyncio.wait_for(_stream(), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            if sys.platform == "win32":
                os.kill(process.pid, signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            process.kill()
        return True, ""
