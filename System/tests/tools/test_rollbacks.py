import os
import sys
import pytest
from System.tools.execution import execute_command_async


@pytest.mark.asyncio
async def test_execution_failure_triggers_rollback(mocker, tmp_path):
    """Proves that a crashing script forces a transactional recovery rollback pass."""
    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()

    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_OS_HEADLESS": "1", "BRAIN_EXECUTION_TIER": "0"}
    )
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(studio_dir)),
    )
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.scan_command", return_value=(True, "Safe")
    )
    mocker.patch(
        "System.neuroanatomy.systemic.microglia.trigger_immune_response_async",
        return_value=(False, "Heal failed"),
    )
    mocker.patch(
        "System.tools.execution.validation.shutil.which",
        return_value="C:\\Windows\\System32\\python.exe"
        if sys.platform == "win32"
        else "/usr/bin/python",
    )

    # Spawn an unpredictable snapshot file in the directory to track cleanup
    leaked_snapshot = studio_dir / ".immutable_snapshot_testfile.py"
    leaked_snapshot.touch()

    # Create a mock process that forcefully exits with an error status (exit code 1)
    mock_process = mocker.AsyncMock()
    mock_process.pid = 9999
    mock_process.returncode = 1
    mock_process.stdout.read = mocker.AsyncMock(
        side_effect=[b"SyntaxError: Crash\n", b""]
    )
    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    spy_rollback = mocker.spy(os, "chmod")

    result = await execute_command_async(["python", "crashing_script.py"], "Studio")

    assert result.success is False
    assert spy_rollback.called, (
        "Security Breakdown: Rollback transactional boundary was not engaged on process failure!"
    )
    assert not leaked_snapshot.exists(), (
        "Security Breakdown: Leaked snapshot file was not scrubbed by rollback operation!"
    )
