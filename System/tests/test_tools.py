from pathlib import Path
from System.tools import (
    write_safe_file,
    read_safe_file,
    list_safe_directory,
    append_safe_file,
    bootstrap_project,
    execute_command,
)


def test_write_safe_file_allowed(tmp_path: Path, mocker) -> None:  # type: ignore
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Professional"})
    result = write_safe_file("Professional/README.md", "# Test")
    assert "SUCCESS" in result
    assert (tmp_path / "Professional/README.md").exists()


def test_security_blocks(tmp_path: Path, mocker) -> None:  # type: ignore
    """Test that writing, reading, and listing outside boundaries are all blocked."""
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Professional"})

    # Test Write Block
    write_result = write_safe_file("System/malicious.py", "print('hacked')")
    assert "SECURITY BLOCK" in write_result

    # Test Read Block
    read_result = read_safe_file(".env")
    assert "SECURITY BLOCK" in read_result

    # Test List Block
    list_result = list_safe_directory("System")
    assert "SECURITY BLOCK" in list_result

    # Test Append Block
    append_result = append_safe_file("System/malicious.py", "print('hacked')")
    assert "SECURITY BLOCK" in append_result


def test_bootstrap_security_block(tmp_path: Path, mocker) -> None:  # type: ignore
    """Ensure archetypes cannot be cloned outside safe boundaries."""
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    result = bootstrap_project("../../malicious_project")
    assert "SECURITY BLOCK" in result


def test_execute_command_security_and_hitl(tmp_path: Path, mocker) -> None:  # type: ignore
    """Ensure shell execution respects directory bounds and requires user confirmation."""
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    studio_dir = tmp_path / "Studio" / "TestProject"
    studio_dir.mkdir(parents=True)

    # 1. Test directory escape block
    block_result = execute_command("ls", "../../")
    assert "SECURITY BLOCK" in block_result

    # 2. Test user denial (HITL)
    mocker.patch("System.tools.Confirm.ask", return_value=False)
    deny_result = execute_command("ls", "Studio/TestProject")
    assert "SECURITY BLOCK" in deny_result

    # 3. Test approved execution
    mocker.patch("System.tools.Confirm.ask", return_value=True)
    mock_subprocess = mocker.patch("System.tools.subprocess.run")
    mock_subprocess.return_value.returncode = 0

    approve_result = execute_command("ls", "Studio/TestProject")
    assert "SUCCESS" in approve_result
    mock_subprocess.assert_called_once()
