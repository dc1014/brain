import os
import pytest
import asyncio
from System.core.locks import BiologicalLock


def test_biological_lock_sync_lifecycle(tmp_path):
    """Proves the synchronous lock acquires memory, writes the file, and cleans up properly."""
    lock_target = tmp_path / "sync_target"
    lock_file = tmp_path / "sync_target.lock"

    lock = BiologicalLock(str(lock_target))

    assert not lock_file.exists()

    with lock:
        assert lock_file.exists()
        content = lock_file.read_text(encoding="utf-8")
        assert str(os.getpid()) in content

    assert not lock_file.exists()


@pytest.mark.asyncio
async def test_biological_lock_async_lifecycle(tmp_path):
    """Proves the asynchronous lock acquires memory, writes the file, and cleans up properly."""
    lock_target = tmp_path / "async_target"
    lock_file = tmp_path / "async_target.lock"

    lock = BiologicalLock(str(lock_target))

    assert not lock_file.exists()

    async with lock:
        assert lock_file.exists()
        content = lock_file.read_text(encoding="utf-8")
        assert str(os.getpid()) in content

    assert not lock_file.exists()


def test_biological_lock_sync_timeout(tmp_path):
    """Proves the synchronous lock times out if blocked."""
    lock_target = tmp_path / "timeout_target"
    lock_file = tmp_path / "timeout_target.lock"

    lock_file.write_text("99999", encoding="utf-8")
    lock = BiologicalLock(str(lock_target), timeout=0.1)

    with pytest.raises(TimeoutError, match="Synaptic Lock Timeout"):
        with lock:
            pass


@pytest.mark.asyncio
async def test_biological_lock_concurrency(tmp_path):
    """Proves multiple async tasks are properly serialized and do not interleave."""
    lock_target = tmp_path / "shared_file"
    shared_list = []

    async def worker(task_id: int):
        lock = BiologicalLock(str(lock_target))
        async with lock:
            shared_list.append(f"start_{task_id}")
            await asyncio.sleep(0.05)
            shared_list.append(f"end_{task_id}")

    await asyncio.gather(worker(1), worker(2))

    assert shared_list == ["start_1", "end_1", "start_2", "end_2"] or shared_list == [
        "start_2",
        "end_2",
        "start_1",
        "end_1",
    ]


def test_biological_lock_medulla_failsafe_fallback(tmp_path, monkeypatch):
    """Proves that instantiating a BiologicalLock with no parameters automatically maps to a safe fallback path."""
    from System.core.locks import BiologicalLock

    # Force ROOT_DIR redirect to test-isolated tmp_path
    monkeypatch.setattr("System.core.locks.ROOT_DIR", tmp_path)

    # Launching parameterless lock - should resolve silently using our failsafe default path
    lock = BiologicalLock()

    assert "brain_master_autonomic.lock" in lock.lock_file
    with lock:
        assert (tmp_path / "Meta" / "brain_master_autonomic.lock").exists()
