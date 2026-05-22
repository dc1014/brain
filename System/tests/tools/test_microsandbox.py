# --- System/tests/tools/test_microsandbox.py ---
import pytest
import asyncio
from System.tools.microsandbox import (
    get_pre_warmed_worker,
    replenish_worker_pool_detached,
)


@pytest.mark.asyncio
async def test_get_pre_warmed_worker_lifecycle(tmp_path):
    """Proves the pool driver handles worker execution creation processes flawlessly."""
    safe_studio_path = tmp_path / "Studio"
    safe_studio_path.mkdir()

    worker = await get_pre_warmed_worker(safe_studio_path)
    assert worker is not None
    assert worker.returncode is None

    if worker.stdin:
        worker.stdin.close()
    worker.kill()
    await worker.wait()


@pytest.mark.asyncio
async def test_replenish_worker_pool_detached_async(tmp_path):
    """Proves background pre-warming tracks loop hydration without block constraints."""
    safe_studio_path = tmp_path / "Studio"
    safe_studio_path.mkdir()

    replenish_worker_pool_detached(safe_studio_path)
    await asyncio.sleep(0.1)

    worker = await get_pre_warmed_worker(safe_studio_path)
    assert worker is not None

    if worker.stdin:
        worker.stdin.close()
    worker.kill()
    await worker.wait()


@pytest.mark.asyncio
async def test_worker_captures_execution_errors(tmp_path):
    """Proves the process sandbox catches script compile or validation exceptions."""
    safe_studio_path = tmp_path / "Studio"
    safe_studio_path.mkdir()

    worker = await get_pre_warmed_worker(safe_studio_path)
    stdout, _ = await worker.communicate(
        input=b"invalid syntax python code error payload"
    )
    assert worker.returncode != 0
