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
    mock_exec.assert_called_once_with("Build app", "FORGE", "STUDIO")


@pytest.mark.asyncio
@patch("System.core.orchestrator.route_sensory_input", new_callable=AsyncMock)
async def test_dispatch_task_rejected(mock_route):
    mock_route.return_value = (False, "Blocked by amygdala", "NONE", "NONE", {})
    with pytest.raises(ValueError, match="Pulse rejected by pre-flight validation"):
        await dispatch_task("Hack mainframe")


@pytest.mark.asyncio
@patch("System.core.orchestrator.read_and_clear_queue")
@patch("System.core.orchestrator._process_all_tasks", new_callable=AsyncMock)
async def test_run_pending_queue(mock_process, mock_read):
    mock_read.return_value = [{"prompt": "Task 1"}]
    await run_pending_queue()
    mock_process.assert_called_once_with([{"prompt": "Task 1"}])


@pytest.mark.asyncio
@patch("System.core.orchestrator.read_and_clear_queue")
@patch("System.core.orchestrator._process_all_tasks", new_callable=AsyncMock)
async def test_run_pending_queue_empty(mock_process, mock_read):
    mock_read.return_value = []
    await run_pending_queue()
    mock_process.assert_not_called()


@pytest.mark.asyncio
@patch("System.core.orchestrator.dispatch_task", new_callable=AsyncMock)
async def test_process_all_tasks(mock_dispatch, tmp_path, monkeypatch):
    monkeypatch.setattr("System.core.orchestrator.ROOT_DIR", tmp_path)
    meta_dir = tmp_path / "Meta"
    meta_dir.mkdir(parents=True)
    pending_file = meta_dir / "Pending_Actions.md"
    pending_file.touch()

    tasks = [
        {"prompt": "Task 1", "route": "R1", "domain": "D1"},
        {"prompt": "Task 2", "route": "R2", "domain": "D2"},
    ]
    await _process_all_tasks(tasks)

    assert mock_dispatch.call_count == 2
    assert not pending_file.exists()
