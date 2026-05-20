# --- System/tests/autonomic/test_quality.py ---
import json
import threading
from pathlib import Path
from System.neuroanatomy.cortical.wernicke import (
    rank_graph_boosted_results,
    SearchResult,
)
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

    # Supply the linked target node so the graph network density formula finds an intersection hit
    mock_search_results: list[SearchResult] = [
        {"filepath": "Studio/UnrelatedNote.md", "score": 10.0, "boosted_score": None},
        {"filepath": "Studio/AuthService.md", "score": 5.0, "boosted_score": None},
        {"filepath": "Studio/TokenEngine.md", "score": 2.0, "boosted_score": None},
    ]

    boosted = rank_graph_boosted_results(mock_search_results, str(graph_file))

    # AuthService shares an active hit link with TokenEngine, boosting its score from 5.0 -> 6.5
    assert boosted[0]["filepath"] == "Studio/UnrelatedNote.md"
    assert boosted[1]["filepath"] == "Studio/AuthService.md"
    assert boosted[1]["boosted_score"] == 6.5


def test_graph_boosted_missing_file_fallback(tmp_path: Path) -> None:
    """Verifies that search records pass through safely if the network map file is missing."""
    non_existent = str(tmp_path / "missing_graph.json")
    mock_results: list[SearchResult] = [
        {"filepath": "Studio/Auth.md", "score": 4.5, "boosted_score": None}
    ]

    res = rank_graph_boosted_results(mock_results, non_existent)
    assert len(res) == 1
    assert res[0]["filepath"] == "Studio/Auth.md"


def test_graph_boosted_corrupted_json_fallback(tmp_path: Path) -> None:
    """Proves that corrupted or invalid JSON graphs are caught without crashing searches."""
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("NOT_VALID_JSON_STRING", encoding="utf-8")

    mock_results: list[SearchResult] = [
        {"filepath": "Studio/Auth.md", "score": 4.5, "boosted_score": None}
    ]
    res = rank_graph_boosted_results(mock_results, str(corrupt_file))
    assert len(res) == 1


def test_write_ahead_log_durable_recovery_cascade(tmp_path: Path) -> None:
    """Verifies that un-completed tasks are accurately surfaced during WAL crash recovery."""
    log_engine = DurableTaskLog(str(tmp_path))

    task_one = log_engine.register_intent("uv run ruff check")
    task_two = log_engine.register_intent("python system_run.py")

    log_engine.mark_completed(task_one, "DONE")

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

    with open(log_engine.wal_path, "w", encoding="utf-8") as f:
        f.write("\n\n")
        f.write('{"invalid_record": true}\n')
        f.write('{"id": "test-id-123", "status": "PENDING", "cmd": "pytest"}\n')

    pending = log_engine.recover_interrupted_tasks()
    assert len(pending) == 1
    assert pending[0]["id"] == "test-id-123"


def test_write_ahead_log_thread_safety_stress(tmp_path: Path) -> None:
    """Stress tests the WAL engine with high concurrent background thread writes."""
    log_engine = DurableTaskLog(str(tmp_path))
    thread_count = 5
    tasks_per_thread = 10

    def worker(worker_id: int) -> None:
        for i in range(tasks_per_thread):
            cmd = f"thread-{worker_id}-cmd-{i}"
            task_id = log_engine.register_intent(cmd)
            if i % 2 == 0:
                log_engine.mark_completed(task_id, "DONE")

    threads = []
    for t_idx in range(thread_count):
        t = threading.Thread(target=worker, args=(t_idx,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    with open(log_engine.wal_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == (thread_count * tasks_per_thread) + (
        thread_count * (tasks_per_thread // 2)
    )
