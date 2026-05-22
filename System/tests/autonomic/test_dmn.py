import pytest
from unittest.mock import patch

from System.neuroanatomy.autonomic.dmn import (
    _gather_dream_context,
    trigger_daydreams,
)


@pytest.fixture
def mock_execute_pipeline():
    """Mocks out the central Prefrontal cortex pipeline execution frame."""
    with patch("System.neuroanatomy.autonomic.dmn.execute_pipeline") as mock_pipeline:

        async def mock_run(payload, route, domain, origin=None):
            return "Task completed."

        mock_pipeline.side_effect = mock_run
        yield mock_pipeline


def test_gather_dream_context(tmp_path):
    with patch("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path):
        daydream_dir = tmp_path / "Meta" / "DMN"
        daydream_dir.mkdir(parents=True, exist_ok=True)
        daydream_file = daydream_dir / "daydreams.md"
        daydream_file.write_text("Existing dream history.", encoding="utf-8")

        log_dir = tmp_path / "System" / "logs"
        log_dir.mkdir(parents=True)
        (log_dir / "experiment_log.md").write_text(
            "System telemetry state.", encoding="utf-8"
        )
        (log_dir / "medulla.log").write_text(
            "Medulla daemon track trace errors.", encoding="utf-8"
        )

        context = _gather_dream_context(daydream_file)
        assert "Existing dream history." in context
        assert "System telemetry state." in context
        assert "Medulla daemon track" in context


def test_gather_dream_context_fallback_option_b(tmp_path):
    with patch("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path):
        daydream_file = tmp_path / "Meta" / "DMN" / "daydreams.md"

        config_dir = tmp_path / "System" / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "agents.yaml").write_text("agents: dispatcher:", encoding="utf-8")

        context = _gather_dream_context(daydream_file)
        assert "CORE SYSTEM CONFIGURATIONS FOR REFLECTION" in context


def test_trigger_daydreams_autonomous_flow(tmp_path, mock_execute_pipeline):
    log_dir = tmp_path / "System" / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "experiment_log.md"
    log_file.write_text("System telemetry trace engram.", encoding="utf-8")

    with patch("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path):
        res = trigger_daydreams(topic=None, domain="STUDIO")
        assert "complete" in res
        assert "Meta/DMN/daydreams.md" in res


def test_trigger_daydreams_directed_topic_flow(tmp_path, mock_execute_pipeline):
    log_dir = tmp_path / "System" / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "experiment_log.md"
    log_file.write_text("Initial log setup metadata lines.", encoding="utf-8")

    with patch("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path):
        res = trigger_daydreams(topic="quantum computing systems", domain="PERSONAL")
        assert "complete" in res
        assert "Meta/DMN/daydreams.md" in res
