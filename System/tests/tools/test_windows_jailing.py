# --- System/tests/tools/test_windows_jailing.py ---
from pathlib import Path
from pytest_mock import MockerFixture
from System.tools.execution import execute_command


def test_windows_job_object_limits_applied(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Proves that native Windows child process lifecycles are constrained by Job Objects."""
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    import os

    mocker.patch.dict(os.environ, {"BRAIN_OS_HEADLESS": "1"})

    # Setup safe isolated script path hooks
    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True, exist_ok=True)

    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(studio_dir)),
    )
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.scan_command", return_value=(True, "Safe")
    )
    mocker.patch("System.tools.execution.sys.platform", "win32")

    # Instantiate safe async sub-process mock templates
    mock_process = mocker.AsyncMock()
    mock_process.pid = 1234
    mock_process.returncode = 0
    mock_process.stdout.read = mocker.AsyncMock(
        side_effect=[b"Mock Win32 Process Output", b""]
    )

    mocker.patch(
        "System.tools.execution.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    # Mock kernel32 system calls using standard ctypes structures safely
    mock_kernel = mocker.MagicMock()
    mock_kernel.CreateJobObjectW.return_value = 0xDEADBEEF
    mock_kernel.SetInformationJobObject.return_value = 1
    mock_kernel.OpenProcess.return_value = 0xAAAA
    mock_kernel.AssignProcessToJobObject.return_value = 1

    mocker.patch("ctypes.windll.kernel32", mock_kernel, create=True)

    result = execute_command("python -version", "Studio")

    assert result.success is True
    assert "Mock Win32 Process Output" in result.output

    # Assert kernel limits were successfully committed into the Windows process scheduler
    mock_kernel.CreateJobObjectW.assert_called_once()
    mock_kernel.SetInformationJobObject.assert_called_once()
    mock_kernel.AssignProcessToJobObject.assert_called_once()
