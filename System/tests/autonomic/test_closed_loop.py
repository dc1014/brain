# --- System/tests/autonomic/test_closed_loop.py ---
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List
from System.neuroanatomy.limbic.hippocampus import SupervisedGraphBackplane
from System.tools.epistemic import verify_trajectory_freshness


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

    # Mock AnteriorCingulateCortex to yield a clear, normal execution status
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

    # Execute with an empty history array to represent a stable system base state
    sgb.supervised_rebuild([])

    # Verify that the knowledge graph is safely generated and serialized
    graph_file = tmp_path / ".brain" / "graph_state.json"
    assert graph_file.exists()

    with open(graph_file, "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    assert isinstance(graph_data, dict)


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
