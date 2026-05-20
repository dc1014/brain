# --- System/tests/autonomic/test_acc.py ---
from pathlib import Path
from typing import Dict, Any, List
from System.neuroanatomy.autonomic.acc import AnteriorCingulateCortex


def test_acc_initialization_fallback(tmp_path: Path, mocker) -> None:
    """Verifies that the ACC initializes cleanly with fallbacks if the config file is missing."""
    mocker.patch("System.neuroanatomy.autonomic.acc.ROOT_DIR", tmp_path)
    acc = AnteriorCingulateCortex()
    assert acc.config["conflict_monitoring"]["max_consecutive_tool_failures"] == 3
    assert acc.tension_score == 0.0


def test_acc_low_stress_chemistry(tmp_path: Path, mocker) -> None:
    """Proves that a history with no failures returns default low-stress parameters."""
    mocker.patch("System.neuroanatomy.autonomic.acc.ROOT_DIR", tmp_path)
    acc = AnteriorCingulateCortex()

    history: List[Dict[str, Any]] = [
        {"tool": "read_safe_file", "status": "SUCCESS"},
        {"tool": "write_safe_file", "status": "SUCCESS"},
    ]

    result = acc.inspect_context_buffer(history)
    assert result["temperature"] == 0.7
    assert result["engine_override"] == "local-slm"
    assert acc.tension_score == 0.0


def test_acc_high_stress_neuromodulation(tmp_path: Path, mocker) -> None:
    """Verifies that consecutive failures increase tension and trigger high-stress parameters."""
    mocker.patch("System.neuroanatomy.autonomic.acc.ROOT_DIR", tmp_path)
    acc = AnteriorCingulateCortex()

    history: List[Dict[str, Any]] = [{"tool": "execute_command", "status": "FAILED"}]

    result = acc.inspect_context_buffer(history)
    assert result["temperature"] == 0.0
    assert result["engine_override"] == "claude-3-5-sonnet"
    assert acc.tension_score > 0.0


def test_acc_circuit_breaker_gating(tmp_path: Path, mocker) -> None:
    """Confirms that hitting maximum consecutive tool failures trips the cognitive circuit breaker."""
    mocker.patch("System.neuroanatomy.autonomic.acc.ROOT_DIR", tmp_path)
    acc = AnteriorCingulateCortex()

    history: List[Dict[str, Any]] = [
        {"tool": "execute_command", "status": "FAILED"},
        {"tool": "execute_command", "status": "FAILED"},
        {"tool": "execute_command", "status": "FAILED"},
    ]

    result = acc.inspect_context_buffer(history)
    assert result["action"] == "FORCE_STRATEGY_SHIFT"
    assert result["clear_context"] is True
    assert result["fallback_archetype"] == "Auditor"
