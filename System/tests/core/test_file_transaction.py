# --- System/tests/core/test_file_transaction.py ---
from System.core.file_transaction import (
    atomic_write,
    atomic_clear,
    read_and_clear_queue,
    read_state_sync,
)


def test_atomic_write(tmp_path):
    """Proves writes operate safely via temporary shadow overlays."""
    test_file = tmp_path / "data.txt"
    atomic_write(test_file, "atomic content")

    assert test_file.exists()
    assert test_file.read_text(encoding="utf-8") == "atomic content"
    # Verify the temporary shadow file was cleanly purged
    assert not test_file.with_suffix(test_file.suffix + ".tmp").exists()


def test_atomic_clear(tmp_path):
    """Proves file blanking occurs cleanly."""
    test_file = tmp_path / "data.txt"
    test_file.write_text("lots of data", encoding="utf-8")

    atomic_clear(test_file)
    assert test_file.read_text(encoding="utf-8") == ""


def test_read_and_clear_queue(tmp_path):
    """Proves JSONL queues can be extracted and blanked simultaneously."""
    queue_file = tmp_path / "queue.jsonl"
    queue_file.write_text('{"task": 1}\n{"task": 2}\n', encoding="utf-8")

    tasks = read_and_clear_queue(queue_file)

    # Verify accurate memory extraction
    assert len(tasks) == 2
    assert tasks[0]["task"] == 1

    # Verify the disk was atomically cleared to prevent double-execution
    assert queue_file.read_text(encoding="utf-8") == ""


def test_read_and_clear_queue_missing_or_corrupted(tmp_path):
    """Ensures queue runners do not crash on invalid JSON lines or missing files."""
    queue_file = tmp_path / "missing.jsonl"
    assert read_and_clear_queue(queue_file) == []

    # Corrupt a single line in the JSONL!
    queue_file.write_text('{"task": 1}\nINVALID_JSON\n{"task": 3}', encoding="utf-8")
    tasks = read_and_clear_queue(queue_file)

    assert len(tasks) == 2  # The corrupted line is safely skipped without crashing
    assert tasks[1]["task"] == 3


def test_read_state_sync(tmp_path):
    """Ensures sync state tracking supports dynamic fallbacks."""
    state_file = tmp_path / "state.json"

    # 1. Missing File
    assert read_state_sync(state_file, dict) == {}

    # 2. Empty Content
    state_file.write_text("   ", encoding="utf-8")
    assert read_state_sync(state_file, list) == []

    # 3. Valid Content
    state_file.write_text('{"key": "value"}', encoding="utf-8")
    assert read_state_sync(state_file, dict) == {"key": "value"}

    # 4. Corrupted Syntax
    state_file.write_text("{{{", encoding="utf-8")
    assert read_state_sync(state_file, list) == []
