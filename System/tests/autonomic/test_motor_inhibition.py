import pytest
import asyncio
from System.core.locks import BiologicalLock
from System.neuroanatomy.autonomic.motor_inhibition import (
    apply_motor_inhibition,
    release_motor_inhibition,
)


@pytest.fixture
def isolated_motor_cortex(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.motor_inhibition.ROOT_DIR", tmp_path
    )
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.motor_inhibition.MD_QUEUE",
        tmp_path / "Personal" / "Pending_Actions.md",
    )
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.motor_inhibition.JSONL_QUEUE",
        tmp_path / "Meta" / "queue.jsonl",
    )
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.motor_inhibition.QUEUE_LOCK",
        BiologicalLock(tmp_path / "Meta" / "hitl_queue"),
    )
    return tmp_path


@pytest.mark.asyncio
async def test_motor_inhibition_approval_flow(isolated_motor_cortex):
    tmp_path = isolated_motor_cortex
    md_file = tmp_path / "Personal" / "Pending_Actions.md"

    inhibition_task = asyncio.create_task(
        apply_motor_inhibition("delete all files", "FORGE", "STUDIO")
    )
    await asyncio.sleep(0.1)

    assert md_file.exists()
    assert "🔴 HIGH" in md_file.read_text(encoding="utf-8")

    approved_count = release_motor_inhibition()
    assert approved_count == 1

    result = await inhibition_task
    assert result is True


@pytest.mark.asyncio
async def test_motor_inhibition_vagus_abort(isolated_motor_cortex):
    tmp_path = isolated_motor_cortex
    inhibition_task = asyncio.create_task(
        apply_motor_inhibition("npm install react", "WORKSPACE", "STUDIO")
    )
    await asyncio.sleep(0.1)

    abort_flag = tmp_path / "System" / ".vagus_abort_signal"
    abort_flag.parent.mkdir(parents=True, exist_ok=True)
    abort_flag.touch()

    result = await inhibition_task
    assert result is False
