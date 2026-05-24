# --- System/tests/autonomic/test_closed_loop.py ---
import json
import pytest
import time
from pathlib import Path
from typing import Any, Dict, List
from System.neuroanatomy.limbic.hippocampus import (
    SupervisedGraphBackplane,
    recall_memory,
    encode_memory,
)
from System.tools.epistemic import verify_trajectory_freshness
from System.neuroanatomy.autonomic.medulla import MedullaOblongata


def test_acc_gates_epistemic_graph_pollution(tmp_path: Path, mocker) -> None:
    """Verifies that the supervised graph backplane successfully blocks link serialization under high cognitive stress."""
    # Initialize mock workspace structure safely
    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True, exist_ok=True)

    # Mock AnteriorCingulateCortex to deterministically simulate an unmanageable strategy shift scenario
    mock_acc_instance = mocker.MagicMock()
    mock_acc_instance.inspect_context_buffer.return_value = {
        "action": "FORCE_STRATEGY_SHIFT",
        "tension": 9.5,
    }
    mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.AnteriorCingulateCortex",
        return_value=mock_acc_instance,
    )

    sgb = SupervisedGraphBackplane(str(tmp_path))

    # Formulate a history payload that hits tension limits
    stuck_history: List[Dict[str, Any]] = [
        {"tool": "execute_command", "status": "FAILED"}
    ]

    # Assert that the circuit breaker trips cleanly and throws the expected RuntimeError
    with pytest.raises(
        RuntimeError, match="Graph write suspended by Anterior Cingulate Cortex"
    ):
        sgb.supervised_rebuild(stuck_history)

    # Verify that graph_state.json was never written to disk, preventing link pollution
    assert not (tmp_path / ".brain" / "graph_state.json").exists()


def test_acc_allows_graph_compilation_under_normal_tension(
    tmp_path: Path, mocker
) -> None:
    """Confirms that graph serialization completes cleanly when system metrics indicate zero cognitive tension."""
    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True, exist_ok=True)

    mock_acc_instance = mocker.MagicMock()
    mock_acc_instance.inspect_context_buffer.return_value = {
        "action": "PROCEED",
        "tension": 1.0,
    }
    mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.AnteriorCingulateCortex",
        return_value=mock_acc_instance,
    )

    sgb = SupervisedGraphBackplane(str(tmp_path))
    sgb.supervised_rebuild([])

    graph_file = tmp_path / ".brain" / "graph_state.json"
    assert graph_file.exists()


def test_trajectory_freshness_drift_detection() -> None:
    """Confirms that stale timeline metrics are accurately flagged as expired by the validity engine."""
    mock_trajectory: List[Dict[str, str]] = [
        {"value": "1200000", "date": "2025-01-01", "valid_until": "2026-01-01"}
    ]

    # Evaluate a 2026 reference check string against an expired 2025 boundary contract
    report = verify_trajectory_freshness(mock_trajectory, "2026-05-19")
    assert report["drift_detected"] is True
    assert report["status"] == "STALE"
    assert report["expired_metric"] == "1200000"


def test_trajectory_freshness_clean_pass() -> None:
    """Validates that active or open-ended trajectory channels report a clean operational status."""
    mock_trajectory: List[Dict[str, str]] = [
        {"value": "2500000", "date": "2026-01-01", "valid_until": "PRESENT"}
    ]

    report = verify_trajectory_freshness(mock_trajectory, "2026-05-19")
    assert report["drift_detected"] is False
    assert report["status"] == "FRESH"


def test_trajectory_freshness_empty_fallback() -> None:
    """Ensures empty structural records pass through smoothly without flagging false drift metrics."""
    report = verify_trajectory_freshness([], "2026-05-19")
    assert report["drift_detected"] is False
    assert report["status"] == "EMPTY"


def test_trajectory_freshness_malformed_bounds() -> None:
    """Asserts that malformed or unparseable date ranges trigger safe drift isolation flags gracefully."""
    mock_trajectory: List[Dict[str, str]] = [
        {"value": "80000", "date": "2026-01-01", "valid_until": "INVALID-DATE-STRING"}
    ]

    report = verify_trajectory_freshness(mock_trajectory, "2026-05-19")
    assert report["drift_detected"] is True
    assert report["status"] == "MALFORMED_BOUNDS"


def test_medulla_wal_closed_loop_recovery_orchestration(tmp_path: Path, mocker) -> None:
    """Verifies that the brainstem daemon accurately intercepts crashed tasks and modulates recovery via the ACC."""
    mocker.patch("System.neuroanatomy.autonomic.medulla.LOG_PATH", tmp_path)
    morphic_medulla = MedullaOblongata()

    # ⚡ ZERO-DEBT FIX: Override the ProcessPoolExecutor with a ThreadPoolExecutor
    # so our Pytest mocks can successfully intercept calls across the concurrent execution boundary!
    from concurrent.futures import ThreadPoolExecutor

    morphic_medulla.recovery_pool = ThreadPoolExecutor(max_workers=1)

    # Seed an interrupted PENDING task command record straight into the Write-Ahead Log ledger

    # Seed an interrupted PENDING task command record straight into the Write-Ahead Log ledger
    _task_id = morphic_medulla.task_log.register_intent(
        "echo 'Resuscitating system...'"
    )

    # Mock the ACC to supply distinct modulated engineering metrics for recovery optimization
    mock_acc_instance = mocker.MagicMock()
    mock_acc_instance.inspect_context_buffer.return_value = {
        "action": "PROCEED",
        "temperature": 0.15,
        "engine_override": "claude-3-5-sonnet",
    }
    # ⚡ SHIFT-LEFT MOCK RESOLUTION: Patch the base definitions module path to fix local function context lookups
    mocker.patch(
        "System.neuroanatomy.autonomic.acc.AnteriorCingulateCortex",
        return_value=mock_acc_instance,
    )

    # Mock subprocess run to simulate background safety completion cleanly
    mock_sub = mocker.patch("subprocess.run")
    mock_sub.return_value.returncode = 0

    # Trigger the boot recovery sequence natively
    morphic_medulla.boot_recovery_sequence()

    # Allow background threading time allocation to execute the runner process frame safely
    time.sleep(0.1)

    # Confirm that the ACC context analysis hook was invoked successfully to optimize variables
    mock_acc_instance.inspect_context_buffer.assert_called_once()

    # Confirm that subprocess received the modulated environment parameters correctly
    _, called_kwargs = mock_sub.call_args
    assert called_kwargs["env"]["BRAIN_RECOVERY_TEMPERATURE"] == "0.15"
    assert called_kwargs["env"]["BRAIN_RECOVERY_ENGINE"] == "claude-3-5-sonnet"


def test_graph_boosted_hybrid_search_integration(tmp_path: Path, mocker) -> None:
    """Proves that recall_memory runs a two-pass hybrid loop and boosts scoring based on link intersections."""
    # Override configuration paths to isolate the test database and ledger
    mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.DB_PATH", tmp_path / "test_hippo.db"
    )
    mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.GRAPH_LEDGER_PATH",
        tmp_path / "graph_state.json",
    )

    # 1. Create a mock relational connection graph ledger map
    graph_state = {
        "Studio/AuthService": [{"rel": "calls", "target": "Studio/TokenEngine"}],
        "Studio/TokenEngine": [],
    }
    with open(tmp_path / "graph_state.json", "w", encoding="utf-8") as f:
        json.dump(graph_state, f)

    # 2. Seed matching lexical memories into our isolated SQLite instance
    encode_memory(
        "Studio/AuthService.md",
        "AuthService authentication engine tokens query text parameters.",
    )
    encode_memory(
        "Studio/TokenEngine.md", "TokenEngine verification loop query text parameters."
    )

    # 3. Trigger recall lookup pass
    search_payload = recall_memory("query")

    # Verify both matched nodes are correctly surfaced and structured with re-rank indicators
    assert "Studio/AuthService.md" in search_payload
    assert "Studio/TokenEngine.md" in search_payload
    assert "Graph Re-Rank Score" in search_payload
