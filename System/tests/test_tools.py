import pytest

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
    """Test that command execution is sandboxed and respects strict HITL."""
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    # SHIFT-LEFT: Guarantee no headless state bleeds into our security test
    mocker.patch.dict("os.environ", {"BRAIN_OS_HEADLESS": "0"}, clear=True)

    studio_dir = tmp_path / "Studio" / "TestProject"
    studio_dir.mkdir(parents=True)

    # 1. Test Security Boundary
    block_result = execute_command("ls", "../../")
    assert "SECURITY BLOCK" in block_result

    # 2. Test HITL Strict Rejection (Standard 'n')
    mocker.patch("builtins.input", return_value="n")
    deny_result = execute_command("ls", "Studio/TestProject")
    assert "SECURITY BLOCK: User explicitly denied" in deny_result

    # 2.5 Test HITL Strict Rejection (Unrecognized garbage input)
    mocker.patch("builtins.input", return_value="garbage_input")
    unrecognized_result = execute_command("ls", "Studio/TestProject")
    assert "SECURITY BLOCK: User explicitly denied" in unrecognized_result

    # 3. Test Execution Approval (Standard 'y')
    mocker.patch("builtins.input", return_value="y")
    mock_subprocess = mocker.patch("System.tools.subprocess.run")
    mock_subprocess.return_value.returncode = 0

    # --- SHIFT-LEFT: Explicitly mock stdout and stderr as empty strings ---
    mock_subprocess.return_value.stdout = ""
    mock_subprocess.return_value.stderr = ""

    approve_result = execute_command("ls", "Studio/TestProject")
    assert "SUCCESS" in approve_result
    assert "<shell_output" in approve_result  # Add this to verify the XML!


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

    # --- SHIFT-LEFT FIX: Clear headless state so HITL is strictly enforced! ---
    monkeypatch.delenv("BRAIN_OS_HEADLESS", raising=False)

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

    # --- SHIFT-LEFT FIX: Mock standard input instead of rich.Confirm ---
    monkeypatch.setattr("builtins.input", lambda *args, **kwargs: "n")

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


def test_search_safe_directory_security_and_metrics(tmp_path: Path, mocker) -> None:  # type: ignore
    """Ensure search_safe_directory finds text, respects the sandbox, and returns telemetry."""
    from System.tools import search_safe_directory

    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch(
        "System.tools.ALLOWED_DIRECTORIES",
        {tmp_path / "Studio", tmp_path / "Professional"},
    )

    # Setup dummy project
    studio_dir = tmp_path / "Studio" / "Project"
    studio_dir.mkdir(parents=True)

    target_file = studio_dir / "marketing.md"
    target_file.write_text("The Open-Core model is our primary strategy.")

    node_modules = studio_dir / "node_modules"
    node_modules.mkdir()
    ignored_file = node_modules / "docs.md"
    ignored_file.write_text("Open-Core")

    # 1. Test Valid Search & Metrics
    result = search_safe_directory("Open-Core", "Studio/Project")
    assert "marketing.md" in result
    assert "node_modules" not in result
    assert "[Telemetry: Scanned" in result  # PROVE telemetry is injected

    # 2. Test Path Traversal Security Block
    block_result = search_safe_directory("password", "../../Windows")
    assert "SECURITY BLOCK" in block_result


def test_analyze_safe_syntax(tmp_path: Path, mocker) -> None:  # type: ignore
    """Ensure analyze_safe_syntax correctly wraps the local linter and respects the sandbox."""
    from System.tools import analyze_safe_syntax

    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True)

    # 1. Test Sandbox block
    assert "SECURITY BLOCK" in analyze_safe_syntax("../../outside.py")

    # 2. Test File Not Found
    assert "ERROR: File" in analyze_safe_syntax("Studio/missing.py")

    # 3. Test Linter Execution (Mocked)
    py_file = studio_dir / "test.py"
    py_file.write_text("print('hello')")

    mock_subprocess = mocker.patch("System.tools.subprocess.run")

    # Simulate Success
    mock_subprocess.return_value = mocker.MagicMock(returncode=0)
    assert "✅ Linter passed" in analyze_safe_syntax("Studio/test.py")

    # Simulate Failure
    mock_subprocess.return_value = mocker.MagicMock(
        returncode=1, stdout="SyntaxError on line 1", stderr=""
    )
    result = analyze_safe_syntax("Studio/test.py")
    assert "❌ Linter found errors" in result
    assert "SyntaxError" in result


def test_read_file_signatures_tool(tmp_path, mocker) -> None:  # type: ignore
    """Ensure the AST scouting tool respects security boundaries and formats correctly."""
    from System.tools import read_file_signatures

    # 1. Setup our mock sandbox
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path})

    test_file = tmp_path / "test_module.py"
    test_file.write_text("def mock_func():\n    print('heavy logic')", encoding="utf-8")

    # 2. Test Security Boundary
    block_result = read_file_signatures("../../test_module.py")
    assert "SECURITY BLOCK" in block_result

    # 3. Test Unsupported File Type
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello", encoding="utf-8")
    txt_result = read_file_signatures("test.txt")
    # Updated to match the new multi-language error message
    assert "ERROR: AST stubbing currently only supports" in txt_result

    # 4. Test Success Path (Brings our coverage back up!)
    success_result = read_file_signatures("test_module.py")
    assert '<document_signatures path="test_module.py">' in success_result
    assert "def mock_func():" in success_result


def test_execute_command_headless_bypass(monkeypatch, tmp_path):
    """Test that setting the headless flag bypasses the HITL prompt for execute_command."""
    from System.tools import execute_command

    # 1. Setup safe path
    safe_dir = tmp_path / "Studio"
    safe_dir.mkdir(parents=True)
    monkeypatch.setattr("System.tools.ROOT_DIR", tmp_path)
    monkeypatch.setattr("System.tools.ALLOWED_DIRECTORIES", {safe_dir})

    # 2. Set the headless override flag
    monkeypatch.setenv("BRAIN_OS_HEADLESS", "1")

    # 3. If the script tries to call input(), intentionally crash the test.
    # This proves the input() block is completely bypassed.
    monkeypatch.setattr(
        "builtins.input", lambda *args: pytest.fail("HITL prompt was not bypassed!")
    )

    # 4. Execute a harmless command
    result = execute_command("echo 'test'", "Studio")

    assert "SECURITY BLOCK" not in result
    assert "<shell_output" in result


def test_operate_forge_headless_bypass(monkeypatch, tmp_path):
    """Test that setting the headless flag bypasses the HITL prompt for operate_forge."""
    from System.tools import operate_forge

    # 1. Setup a fake Forge project
    project_dir = tmp_path / "Studio" / "TestProject"
    project_dir.mkdir(parents=True)
    (project_dir / "orchestrator.py").touch()
    monkeypatch.setattr("System.tools.ROOT_DIR", tmp_path)
    monkeypatch.setattr("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    # 2. Mock execution to do nothing but succeed
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type("MockResult", (), {"returncode": 0})(),
    )

    # 3. Set the headless flag and crash if input() is called
    monkeypatch.setenv("BRAIN_OS_HEADLESS", "1")
    monkeypatch.setattr(
        "builtins.input", lambda *args: pytest.fail("HITL prompt was not bypassed!")
    )

    result = operate_forge("TestProject", "Do something")

    assert "SECURITY BLOCK" not in result
    assert "FORGE EXECUTION COMPLETE" in result


def test_sense_environment_tool(monkeypatch):
    """Proves the Brain can successfully invoke the external Sense organ and return Hybrid XML/MD."""
    from System.tools import sense_environment

    # 1. Mock a successful transduction
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type(
            "MockResult",
            (),
            {
                "returncode": 0,
                "stdout": '<sensory_input source="https://example.com">\n# Mock Webpage\n</sensory_input>',
                "stderr": "",
            },
        )(),
    )
    result = sense_environment("https://example.com")
    assert "<sensory_input" in result
    assert "# Mock Webpage" in result

    # 2. Mock a blocked SSRF attempt
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type(
            "MockResult",
            (),
            {
                "returncode": 1,
                "stdout": "<sensory_error>\nSSRF Block\n</sensory_error>",
                "stderr": "",
            },
        )(),
    )
    error_result = sense_environment("http://localhost")
    assert "<sensory_error" in error_result
    assert "SSRF Block" in error_result


def test_tools_yaml_schema_validity():
    import yaml  # type: ignore
    from pathlib import Path

    yaml_path = Path(__file__).parent.parent / "config" / "tools.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        tools = yaml.safe_load(f)

    # Ensure every tool has valid OpenAI schema fields
    for group_name, tool_list in tools.items():
        for tool in tool_list:
            assert "type" in tool
            assert "function" in tool
            assert "name" in tool["function"]
            assert "parameters" in tool["function"]
            assert "properties" in tool["function"]["parameters"]
