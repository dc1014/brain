from unittest.mock import MagicMock
from System.neuroanatomy.autonomic.dmn import (
    enforce_rem_paralysis,
    wake_from_rem,
    _get_current_branch,
)


def test_get_current_branch(mocker, tmp_path):
    """Proves the DMN correctly identifies the pre-sleep reality state."""
    mock_run = mocker.patch("System.neuroanatomy.autonomic.dmn.subprocess.run")
    mock_res = MagicMock()
    mock_res.stdout = "feature/test-branch\n"
    mock_run.return_value = mock_res

    branch = _get_current_branch(tmp_path)
    assert branch == "feature/test-branch"


def test_enforce_rem_paralysis_success(mocker, tmp_path, monkeypatch):
    """Proves the system triggers REM paralysis and traps the agent in a new branch."""
    monkeypatch.setattr("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path)
    project_dir = tmp_path / "Studio" / "TestProject"
    project_dir.mkdir(parents=True)

    mock_run = mocker.patch("System.neuroanatomy.autonomic.dmn.subprocess.run")

    # Mocking sequential subprocess calls: git status -> rev-parse -> checkout -b
    mock_status = MagicMock(returncode=0)
    mock_rev_parse = MagicMock(returncode=0, stdout="main\n")
    mock_checkout = MagicMock(returncode=0)
    mock_run.side_effect = [mock_status, mock_rev_parse, mock_checkout]

    dream_branch, orig_branch = enforce_rem_paralysis("TestProject")

    assert orig_branch == "main"
    assert dream_branch is not None and dream_branch.startswith("dream/hypothesis_")
    assert mock_run.call_count == 3


def test_wake_from_rem(mocker, tmp_path, monkeypatch):
    """Proves the system safely commits the hallucination and checks out the original branch."""
    monkeypatch.setattr("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path)
    project_dir = tmp_path / "Studio" / "TestProject"
    project_dir.mkdir(parents=True)

    mock_run = mocker.patch("System.neuroanatomy.autonomic.dmn.subprocess.run")
    mock_checkout = MagicMock(returncode=0)
    mock_run.return_value = mock_checkout

    wake_from_rem("TestProject", "dream/hypothesis_123", "main")

    # Should call: git add -> git commit -> git checkout
    assert mock_run.call_count == 3
    mock_run.assert_called_with(
        ["git", "checkout", "main"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )
