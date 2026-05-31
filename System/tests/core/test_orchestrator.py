# --- System/tests/core/test_orchestrator.py ---
import pytest
from unittest.mock import AsyncMock, patch
from System.core.orchestrator import (
    dispatch_task,
    run_pending_queue,
    _process_all_tasks,
)


@pytest.mark.asyncio
@patch("System.core.orchestrator.route_sensory_input", new_callable=AsyncMock)
@patch("System.core.orchestrator.execute_pipeline", new_callable=AsyncMock)
async def test_dispatch_task_success(mock_exec, mock_route):
    mock_route.return_value = (True, "OK", "FORGE", "STUDIO", {})
    await dispatch_task("Build app")
    mock_exec.assert_called_once_with("Build app", "FORGE", "STUDIO", goal_thread=None)


@pytest.mark.asyncio
@patch("System.core.orchestrator.route_sensory_input", new_callable=AsyncMock)
async def test_dispatch_task_rejected(mock_route):
    mock_route.return_value = (False, "Blocked by amygdala", "NONE", "NONE", {})
    with pytest.raises(ValueError, match="Pulse rejected by pre-flight validation"):
        await dispatch_task("Hack mainframe")


@pytest.mark.asyncio
@patch("System.core.orchestrator._process_all_tasks", new_callable=AsyncMock)
async def test_run_pending_queue_parses_markdown(mock_process, tmp_path, monkeypatch):
    """Proves the orchestrator successfully extracts tasks directly from Markdown."""
    monkeypatch.setattr("System.core.orchestrator.ROOT_DIR", tmp_path)
    meta_dir = tmp_path / "Meta"
    meta_dir.mkdir(parents=True)
    pending_file = meta_dir / "Pending_Actions.md"

    # Write a valid markdown block matching the UX format
    pending_content = (
        "### ⏳ Pending Task (2026-05-30)\n"
        "**Prompt:** Build a new feature\n"
        "**Thalamus Route:** `CODE_GENERATION` | **Domain:** `STUDIO`\n"
        "> **Threat Analysis & Reasoning:** Route auto-calculated.\n---\n"
    )
    pending_file.write_text(pending_content, encoding="utf-8")

    await run_pending_queue()

    # Verify the regex parser extracted the right payload
    expected_tasks = [
        {
            "prompt": "Build a new feature",
            "route": "CODE_GENERATION",
            "domain": "STUDIO",
            "goal_thread": None,
        }
    ]
    mock_process.assert_called_once_with(expected_tasks)

    # Verify the file was safely archived into the completed ledger
    completed_file = meta_dir / "Completed_Actions.md"
    assert completed_file.exists()
    assert "Build a new feature" in completed_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
@patch("System.core.orchestrator._process_all_tasks", new_callable=AsyncMock)
async def test_run_pending_queue_empty(mock_process, tmp_path, monkeypatch):
    """Proves the orchestrator bails out cleanly if the queue file is missing."""
    monkeypatch.setattr("System.core.orchestrator.ROOT_DIR", tmp_path)
    await run_pending_queue()
    mock_process.assert_not_called()


@pytest.mark.asyncio
@patch("System.core.orchestrator.dispatch_task", new_callable=AsyncMock)
async def test_process_all_tasks(mock_dispatch, tmp_path, monkeypatch):
    """Proves the subprocess execution loops over the extracted markdown payloads."""
    monkeypatch.setattr("System.core.orchestrator.ROOT_DIR", tmp_path)

    tasks = [
        {"prompt": "Task 1", "route": "R1", "domain": "D1"},
        {"prompt": "Task 2", "route": "R2", "domain": "D2"},
    ]
    await _process_all_tasks(tasks)

    assert mock_dispatch.call_count == 2
