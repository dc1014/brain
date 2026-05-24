import pytest
import os
from System.tools.execution import execute_command_async


@pytest.mark.asyncio
async def test_native_execution_enforces_read_only_volume_mask(mocker, tmp_path):
    """Proves that native process execution engages the volume mask tool boundary."""
    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()

    # Setup dummy fake system core file to verify permissions tracking
    fake_system_dir = tmp_path / "System"
    fake_system_dir.mkdir()
    fake_core_file = fake_system_dir / "paths.py"
    fake_core_file.write_text("ROOT_DIR = '.'")

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

    # Mock the subprocess execution engine to instantly pass
    mock_process = mocker.AsyncMock()
    mock_process.pid = 9999
    mock_process.returncode = 0
    mock_process.stdout.read = mocker.AsyncMock(side_effect=[b"Success", b""])
    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    # Spy on the volume mask lifecycle
    spy_chmod = mocker.spy(os, "chmod")

    result = await execute_command_async(["echo", "Volume Protection Active"], "Studio")

    assert result.success is True
    assert spy_chmod.called, (
        "Security Breakdown: The system volume protection mask was never activated!"
    )
