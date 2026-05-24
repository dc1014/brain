# --- System/tests/core/test_file_transaction.py ---
import pytest
import os
from pathlib import Path
from System.core.file_transaction import (
    read_state_sync,
    read_state_async,
    write_state_sync_atomic,
    write_state_async_atomic,
)


def test_read_state_sync_nonexistent_fallback(tmp_path: Path) -> None:
    """Proves reading a missing file safely returns the provided factory default structure."""
    target_file = tmp_path / "missing_queue.json"

    # Test dictionary factory default
    dict_data = read_state_sync(target_file, default_factory=dict)
    assert dict_data == {}
    assert isinstance(dict_data, dict)

    # Test list factory default
    list_data = read_state_sync(target_file, default_factory=list)
    assert list_data == []
    assert isinstance(list_data, list)


@pytest.mark.asyncio
async def test_read_state_async_nonexistent_fallback(tmp_path: Path) -> None:
    """Proves asynchronous reading of a missing file safely returns factory defaults."""
    target_file = tmp_path / "missing_async.json"

    data = await read_state_async(target_file, default_factory=dict)
    assert data == {}


def test_write_and_read_state_sync_atomic_json(tmp_path: Path) -> None:
    """Validates full synchronous serialization, atomic replacement, and lock-guarded read cycles."""
    target_file = tmp_path / "system_state.json"
    sample_payload = {
        "status": "RUNNING",
        "active_nodes": ["prefrontal", "thalamus"],
        "metadata": {"cycle_count": 42},
    }

    # Execute atomic sync write
    write_state_sync_atomic(target_file, sample_payload)
    assert target_file.exists()

    # Execute sync transaction read
    loaded_payload = read_state_sync(target_file, default_factory=dict)
    assert loaded_payload == sample_payload
    assert loaded_payload["metadata"]["cycle_count"] == 42


@pytest.mark.asyncio
async def test_write_and_read_state_async_atomic_json(tmp_path: Path) -> None:
    """Validates full asynchronous serialization, atomic replacement, and lock-guarded read cycles."""
    target_file = tmp_path / "system_state_async.json"
    sample_payload = [{"task_id": "tx_99", "priority": "high"}]

    # Execute atomic async write
    await write_state_async_atomic(target_file, sample_payload)
    assert target_file.exists()

    # Execute async transaction read
    loaded_payload = await read_state_async(target_file, default_factory=list)
    assert loaded_payload == sample_payload


def test_strict_utf8_unicode_preservation_windows_trap(tmp_path: Path) -> None:
    """Guarantees multi-byte characters and complex symbols survive write/read boundaries cleanly."""
    target_file = tmp_path / "autobiography.md"

    # Inject multi-byte glyphs, symbols, and mathematical constants (The ultimate Windows Trap test vector)
    unicode_stimulus = (
        "🧠 Biomimetic Agentic OS Core Loop Active 🚀 ∑(Tokens) = Metabolism 🧬"
    )

    write_state_sync_atomic(target_file, unicode_stimulus)

    # Read back to ensure no fallback code-page corruption occurred
    loaded_string = read_state_sync(target_file, default_factory=str)
    assert loaded_string == unicode_stimulus


def test_atomic_file_swap_lifecycle_cleanliness(tmp_path: Path, mocker) -> None:
    """Proves temporary sibling `.tmp` working files are completely scrubbed from disk post-swap."""
    target_file = tmp_path / "execution_queue.json"
    payload = {"queue": "clear"}

    # Spy on os.replace to verify the swap mechanics
    spy_replace = mocker.spy(os, "replace")

    write_state_sync_atomic(target_file, payload)

    # Ensure os.replace was invoked to process the update atomically
    assert spy_replace.call_count == 1

    # Ensure no leftover temporary garbage or residue artifacts pollute the working folder block
    sibling_files = list(tmp_path.glob(".*.tmp"))
    assert len(sibling_files) == 0, (
        "Atomic temporary swap residue leaked to persistent storage layer."
    )
