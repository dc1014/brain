from pathlib import Path
from System.tools import write_safe_file


def test_write_safe_file_allowed(tmp_path: Path, mocker) -> None:  # type: ignore
    """Test that writing to an allowed directory succeeds."""
    # Mock the root and allowed directories to a safe temporary testing path
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Professional"})

    result = write_safe_file("Professional/Business_Plan/README.md", "# Test")
    assert "SUCCESS" in result
    assert (tmp_path / "Professional/Business_Plan/README.md").exists()


def test_write_safe_file_blocked_system(tmp_path: Path, mocker) -> None:  # type: ignore
    """Test that writing to the System folder is strictly blocked."""
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Professional"})

    result = write_safe_file("System/malicious.py", "print('hacked')")
    assert "SECURITY BLOCK" in result
    assert not (tmp_path / "System/malicious.py").exists()


def test_write_safe_file_blocked_traversal(tmp_path: Path, mocker) -> None:  # type: ignore
    """Test that a directory traversal attack (../) is caught and blocked."""
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Professional"})

    # Simulate an AI trying to back out of the allowed folder to overwrite the .env
    result = write_safe_file("Professional/../../.env", "HACKED_KEY=123")
    assert "SECURITY BLOCK" in result
