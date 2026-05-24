import pytest
import asyncio
from pathlib import Path
from System.core.locks import BiologicalLock


@pytest.mark.asyncio
async def test_biological_lock_mutual_exclusion(tmp_path: Path):
    """Proves that multiple async workers cannot write to the same file simultaneously."""
    target_file = tmp_path / "shared_memory.txt"
    lock = BiologicalLock(target_file)

    writes = []

    async def worker_1():
        async with lock.acquire():
            writes.append("Worker 1 Start")
            await asyncio.sleep(0.1)  # Simulate slow I/O
            writes.append("Worker 1 End")

    async def worker_2():
        await asyncio.sleep(0.02)  # Give worker 1 a split-second head start
        async with lock.acquire():
            writes.append("Worker 2 Start")
            writes.append("Worker 2 End")

    await asyncio.gather(worker_1(), worker_2())

    # If the lock failed, Worker 2 would interject between Worker 1's Start/End
    assert writes == [
        "Worker 1 Start",
        "Worker 1 End",
        "Worker 2 Start",
        "Worker 2 End",
    ]


@pytest.mark.asyncio
async def test_biological_lock_timeout(tmp_path: Path):
    """Proves the lock throws a safe timeout if the file is permanently deadlocked."""
    from filelock import Timeout

    target_file = tmp_path / "deadlock.txt"
    lock1 = BiologicalLock(target_file, timeout=0.1)
    lock2 = BiologicalLock(target_file, timeout=0.1)

    # Deterministically simulate a cross-process lock contention block
    def mock_acquire_timeout(*args, **kwargs):
        raise Timeout(str(lock2.lock_path))

    lock2.file_lock.acquire = mock_acquire_timeout  # type: ignore[method-assign]

    async def hold_lock_forever():
        async with lock1.acquire():
            await asyncio.sleep(0.1)

    async def try_to_steal_lock():
        await asyncio.sleep(0.02)
        with pytest.raises(Timeout):
            async with lock2.acquire():
                pass

    await asyncio.gather(hold_lock_forever(), try_to_steal_lock())
