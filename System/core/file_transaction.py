import os
import json
import asyncio
from pathlib import Path
from typing import Any
from System.core.locks import BiologicalLock


def read_state_sync(filepath: str | Path, default_factory: Any = dict) -> Any:
    """Synchronously reads a state file with explicit UTF-8 parsing under IPC lock protection."""
    target = Path(filepath).resolve()
    if not target.exists():
        return default_factory()

    lock = BiologicalLock(target)
    with lock.acquire_sync():
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default_factory()
                if target.suffix == ".json":
                    return json.loads(content)
                return content
        except Exception:
            return default_factory()


async def read_state_async(filepath: str | Path, default_factory: Any = dict) -> Any:
    """Asynchronously reads a state file with explicit UTF-8 parsing under async/IPC lock protection."""
    target = Path(filepath).resolve()
    if not target.exists():
        return default_factory()

    lock = BiologicalLock(target)
    async with lock.acquire():
        try:
            # Shift blocking I/O off the main event loop cleanly
            def _read():
                with open(target, "r", encoding="utf-8") as f:
                    return f.read().strip()

            content = await asyncio.to_thread(_read)
            if not content:
                return default_factory()
            if target.suffix == ".json":
                return json.loads(content)
            return content
        except Exception:
            return default_factory()


def write_state_sync_atomic(filepath: str | Path, data: Any) -> None:
    """Synchronously writes content via an atomic temporary-file swap with strict UTF-8 enforcement."""
    target = Path(filepath).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    # Generate temporary sibling file on the same mount-point to guarantee atomic rename operations
    temp_file = target.with_name(f".{target.name}.tmp")

    # Serialize data beforehand to keep lock holding durations at absolute minimum
    content = (
        json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
    )

    lock = BiologicalLock(target)
    with lock.acquire_sync():
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(
                    f.fileno()
                )  # Force OS buffer cache flush to persistent storage platters

            # Atomic swap operation: guarantees zero truncation or partial-write states
            os.replace(temp_file, target)
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass


async def write_state_async_atomic(filepath: str | Path, data: Any) -> None:
    """Asynchronously writes content via an atomic temporary-file swap with strict UTF-8 enforcement."""
    target = Path(filepath).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_file = target.with_name(f".{target.name}.tmp")

    content = (
        json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
    )

    lock = BiologicalLock(target)
    async with lock.acquire():
        try:

            def _write_and_sync():
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_file, target)

            await asyncio.to_thread(_write_and_sync)
        finally:

            def _cleanup():
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except OSError:
                        pass

            await asyncio.to_thread(_cleanup)
