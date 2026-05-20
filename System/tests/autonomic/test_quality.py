# --- System/tests/autonomic/test_quality.py ---
import json
from pathlib import Path
from System.neuroanatomy.cortical.wernicke import rank_graph_boosted_results
from System.neuroanatomy.autonomic.medulla import DurableTaskLog


def test_graph_boosted_reranking_density(tmp_path: Path) -> None:
    """Confirms that search results are accurately boosted based on network graph density."""
    graph_file = tmp_path / "graph_state.json"
    graph_state = {
        "Studio/AuthService": [{"rel": "calls", "target": "Studio/TokenEngine"}],
        "Studio/TokenEngine": [],
    }
    with open(graph_file, "w", encoding="utf-8") as f:
        json.dump(graph_state, f)

    mock_search_results = [
        {"filepath": "Studio/UnrelatedNote.md", "score": 10.0},
        {"filepath": "Studio/AuthService.md", "score": 5.0},
        {"filepath": "Studio/TokenEngine.md", "score": 2.0},
    ]

    boosted = rank_graph_boosted_results(mock_search_results, str(graph_file))

    # AuthService shares an active hit link with TokenEngine, receiving an explicit +1.5 boost factor
    assert boosted[0]["filepath"] == "Studio/UnrelatedNote.md"  # Score remains 10.0
    assert (
        boosted[1]["filepath"] == "Studio/AuthService.md"
    )  # Score boosted from 5.0 -> 6.5
    assert boosted[1]["boosted_score"] == 6.5


def test_graph_boosted_missing_file_fallback(tmp_path: Path) -> None:
    """Verifies that search records pass through safely if the network map file is missing."""
    non_existent = str(tmp_path / "missing_graph.json")
    mock_results = [{"filepath": "Studio/Auth.md", "score": 4.5}]

    res = rank_graph_boosted_results(mock_results, non_existent)
    assert res == mock_results


def test_graph_boosted_corrupted_json_fallback(tmp_path: Path) -> None:
    """Proves that corrupted or invalid JSON graphs are caught without crashing searches."""
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("NOT_VALID_JSON_STRING", encoding="utf-8")

    mock_results = [{"filepath": "Studio/Auth.md", "score": 4.5}]
    res = rank_graph_boosted_results(mock_results, str(corrupt_file))
    assert res == mock_results


def test_write_ahead_log_durable_recovery_cascade(tmp_path: Path) -> None:
    """Verifies that un-completed tasks are accurately surfaced during WAL crash recovery."""
    log_engine = DurableTaskLog(str(tmp_path))

    # 1. Register two intents
    task_one = log_engine.register_intent("uv run ruff check")
    task_two = log_engine.register_intent("python system_run.py")

    # 2. Mark only task one as completed cleanly
    log_engine.mark_completed(task_one, "DONE")

    # 3. Simulate system reboot recovery sweep check
    pending_recovery = log_engine.recover_interrupted_tasks()

    assert len(pending_recovery) == 1
    assert pending_recovery[0]["id"] == task_two
    assert pending_recovery[0]["cmd"] == "python system_run.py"


def test_write_ahead_log_missing_file_recovery(tmp_path: Path) -> None:
    """Confirms recovery returns an empty array if the WAL file does not exist yet."""
    log_engine = DurableTaskLog(str(tmp_path / "empty_logs"))
    assert log_engine.recover_interrupted_tasks() == []


def test_write_ahead_log_handles_empty_or_broken_lines(tmp_path: Path) -> None:
    """Ensures that empty whitespace entries or malformed lines inside logs are handled cleanly."""
    log_engine = DurableTaskLog(str(tmp_path))

    # Append unparseable text lines directly onto the log ledger stream
    with open(log_engine.wal_path, "w", encoding="utf-8") as f:
        f.write("\n\n")
        f.write('{"invalid_record": true}\n')
        f.write('{"id": "test-id-123", "status": "PENDING", "cmd": "pytest"}\n')

    pending = log_engine.recover_interrupted_tasks()
    assert len(pending) == 1
    assert pending[0]["id"] == "test-id-123"
