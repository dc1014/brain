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


def test_adr_safety_blocks() -> None:
    """Ensure the AI cannot autonomously write, append, or rename ADR files."""
    from System.tools import append_safe_file, rename_safe_file, write_safe_file

    # Test Write Block
    write_res = write_safe_file("Studio/Project/docs/adr/001-test.md", "data")
    assert "SECURITY BLOCK" in write_res

    # Test Append Block
    append_res = append_safe_file("Studio/Project/docs/adr/001-test.md", "data")
    assert "SECURITY BLOCK" in append_res

    # Test Rename (Move existing ADR out) Block
    rename_res_1 = rename_safe_file(
        "Studio/Project/docs/adr/001-test.md", "Studio/Project/new.md"
    )
    assert "SECURITY BLOCK" in rename_res_1
    assert "Cannot modify, move, or create ADRs" in rename_res_1

    # Test Rename (Move random file into ADR folder) Block
    rename_res_2 = rename_safe_file(
        "Studio/Project/old.md", "Studio/Project/docs/adr/002-test.md"
    )
    assert "SECURITY BLOCK" in rename_res_2


def test_operate_forge_security(tmp_path, monkeypatch) -> None:
    """Ensure operate_forge enforces path safety and HITL approvals."""
    from System.tools import operate_forge
    import System.tools as tools
    from pathlib import Path

    # 1. Test Path Traversal Block
    res_path = operate_forge("../../../Windows", "Build stuff")
    assert "SECURITY BLOCK" in res_path

    # Mock the safe path using a real, OS-resolved temporary directory
    mock_root = tmp_path.resolve()
    monkeypatch.setattr(tools, "ROOT_DIR", mock_root)
    monkeypatch.setattr(tools, "is_safe_path", lambda x: True)

    # 2. Test Missing Engine Block
    res_missing = operate_forge("Empty-Project", "Build stuff")
    assert "ERROR: Forge engine not found" in res_missing

    # 3. Test HITL Denial Block
    # Create the dummy directory and file so it passes the .exists() check
    dummy_project = mock_root / "Studio" / "Mock-Project"
    dummy_project.mkdir(parents=True)
    (dummy_project / "orchestrator.py").touch()

    # Mock the user pressing 'n' on the prompt
    monkeypatch.setattr(tools.Confirm, "ask", lambda *args, **kwargs: False)

    # Prevent the test from actually trying to write handoff.md
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: None)

    res_denied = operate_forge("Mock-Project", "Build stuff")
    assert "SECURITY BLOCK: User explicitly denied" in res_denied


def test_copy_safe_file_security(tmp_path: Path, mocker) -> None:  # type: ignore
    """Ensure copy_safe_file blocks path traversal and protects ADRs."""
    from System.tools import copy_safe_file

    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch(
        "System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Media", tmp_path / "Studio"}
    )

    # Setup dummy source file
    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    source_file = media_dir / "logo.png"
    source_file.write_text("dummy binary data")

    # 1. Test Valid Copy
    result = copy_safe_file("Media/logo.png", "Studio/logo.png")
    assert "SUCCESS" in result
    assert (tmp_path / "Studio/logo.png").exists()

    # 2. Test Path Traversal Security Block
    block_result = copy_safe_file("Media/logo.png", "../../Windows/System32/hacked.png")
    assert "SECURITY BLOCK" in block_result

    # 3. Test ADR Protection
    adr_dir = tmp_path / "Studio" / "adr"
    adr_dir.mkdir(parents=True)
    adr_file = adr_dir / "001-architecture.md"
    adr_file.write_text("secret architecture")

    adr_block = copy_safe_file("Studio/adr/001-architecture.md", "Studio/stolen.md")
    assert "SECURITY BLOCK: Cannot copy ADRs." in adr_block
