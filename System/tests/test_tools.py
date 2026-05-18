import pytest

from pathlib import Path
from System.tools import (
    write_safe_file,
    read_safe_file,
    list_safe_directory,
    append_safe_file,
    bootstrap_project,
    execute_command,
    write_multiple_files,
)
from System.tools.execution import manage_background_process
from System.tools.diagnostic import get_system_vitals
from unittest.mock import patch


@patch("System.neuroanatomy.peripheral.motor.log_metabolism")
def test_write_safe_file_allowed(mock_log, tmp_path: Path, mocker) -> None:  # type: ignore

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch(
        "System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Professional"}
    )
    result = write_safe_file("Professional/README.md", "# Test")
    assert "SUCCESS" in result
    assert (tmp_path / "Professional/README.md").exists()


@patch("System.neuroanatomy.peripheral.motor.log_metabolism")
def test_security_blocks(mock_log, tmp_path: Path, mocker) -> None:  # type: ignore
    """Test that writing, reading, and listing outside boundaries are all blocked."""

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch(
        "System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Professional"}
    )

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

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    result = bootstrap_project("../../malicious_project")
    assert "SECURITY BLOCK" in result


def test_execute_command_security_and_hitl(tmp_path: Path, mocker) -> None:  # type: ignore
    """Test that command execution is sandboxed and respects strict HITL."""

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})
    mocker.patch.dict("os.environ", {"BRAIN_OS_HEADLESS": "0"}, clear=True)

    studio_dir = tmp_path / "Studio" / "TestProject"
    studio_dir.mkdir(parents=True, exist_ok=True)

    block_result = execute_command("ls", "../../")
    assert "PATH TRAVERSAL BLOCKED" in block_result

    # Add 'mocker' to the parameters
    # ... end of test_execute_command_security_and_hitl ...
    # (Make sure to remove the accidentally pasted test_adr_safety_blocks from inside it!)


@patch("System.neuroanatomy.peripheral.motor.log_metabolism")
def test_adr_safety_blocks(mock_log, mocker) -> None:
    """Ensure the AI cannot autonomously write, append, or rename ADR files."""
    from System.tools import append_safe_file, rename_safe_file, write_safe_file

    # Bypass the sandbox so we hit the ADR check!
    mocker.patch("System.tools.file_system.is_safe_path", return_value=True)

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
    monkeypatch.setattr(
        "System.tools.forge.is_safe_path", lambda x, require_write=False: True
    )

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

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch(
        "System.tools.sandbox.ALLOWED_DIRECTORIES",
        {tmp_path / "Media", tmp_path / "Studio"},
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

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch(
        "System.tools.sandbox.ALLOWED_DIRECTORIES",
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

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True)

    # 1. Test Sandbox block
    assert "SECURITY BLOCK" in analyze_safe_syntax("../../outside.py")

    # 2. Test File Not Found
    assert "ERROR: File" in analyze_safe_syntax("Studio/missing.py")

    # 3. Test Linter Execution (Mocked)
    py_file = studio_dir / "test.py"
    py_file.write_text("print('hello')")

    mock_subprocess = mocker.patch("System.tools.execution.subprocess.run")

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

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path})

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
    """Test that setting the headless flag bypasses the HITL prompt."""
    import pytest

    safe_dir = tmp_path / "Studio"
    safe_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.blood_brain_barrier.ROOT_DIR", tmp_path
    )
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        lambda x: (True, str(safe_dir)),
    )

    monkeypatch.setenv("BRAIN_OS_HEADLESS", "1")
    # ... rest of the test ...

    monkeypatch.setattr(
        "builtins.input", lambda *args: pytest.fail("HITL prompt was not bypassed!")
    )

    result = execute_command("python --version", "Studio")

    assert "PATH TRAVERSAL BLOCKED" not in result
    assert "<shell_output>" in result  # Check for the restored XML contract


def test_operate_forge_headless_bypass(monkeypatch, tmp_path):
    """Test that setting the headless flag bypasses the HITL prompt for operate_forge."""
    from System.tools import operate_forge

    # 1. Setup a fake Forge project
    project_dir = tmp_path / "Studio" / "TestProject"
    project_dir.mkdir(parents=True)
    (project_dir / "orchestrator.py").touch()
    monkeypatch.setattr("System.tools.file_system.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Studio"}
    )

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


def test_speak(mocker):
    from System.tools import speak

    mocker.patch("System.neuroanatomy.cortical.broca.synthesize_speech")
    mocker.patch("Sense.receptors.audio.play_audio")

    res = speak("Hello")
    assert "SUCCESS" in res


def test_analyze_audio(tmp_path, mocker):
    from System.tools import analyze_audio

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path})

    fake_audio = tmp_path / "test.wav"
    fake_audio.write_text("fake binary")

    mocker.patch(
        "System.neuroanatomy.cortical.wernicke.transcribe_speech",
        return_value="Speech text.",
    )
    mocker.patch(
        "System.neuroanatomy.cortical.temporal_lobe.comprehend_sound",
        return_value="Bird sound.",
    )

    res = analyze_audio("test.wav")
    assert "Speech text" in res
    assert "Bird sound" in res


def test_deploy_project(tmp_path: Path, mocker) -> None:  # type: ignore
    """Ensures the generic deployment tool respects the Vault, HITL, and the Sandbox."""
    from System.tools.execution import deploy_project
    from System.core.schemas import ExecutionResult

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.ROOT_DIR", tmp_path)
    mocker.patch("System.neuroanatomy.systemic.blood_brain_barrier.ROOT_DIR", tmp_path)

    studio_dir = tmp_path / "Studio" / "WebProject"
    studio_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(studio_dir)),
    )

    # 1. Test Missing Token (Vault Block)
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret", return_value=None
    )
    result_no_token = deploy_project(str(studio_dir))
    assert isinstance(result_no_token, ExecutionResult)
    assert not result_no_token.success
    assert "DEPLOYMENT_TOKEN is missing" in result_no_token.output

    # 2. Test Human Rejection
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret",
        return_value="fake_deployment_token",
    )
    mocker.patch.dict("os.environ", {"BRAIN_OS_HEADLESS": "0"}, clear=True)
    mocker.patch("builtins.input", return_value="n")

    result_denied = deploy_project(str(studio_dir))
    assert not result_denied.success
    assert "User explicitly denied" in result_denied.output

    # 3. Test Successful Simulated Deployment
    mocker.patch("builtins.input", return_value="y")
    mock_popen = mocker.patch("System.tools.execution.subprocess.Popen")
    mock_process = mocker.MagicMock()
    mock_process.stdout = [
        "Deploying...\n",
        "Production: https://brain-os.simulated.app\n",
    ]
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    result_success = deploy_project(str(studio_dir), provider="custom")
    assert result_success.success
    assert "<deployment_success>" in result_success.output
    assert "https://brain-os.simulated.app" in result_success.output


def test_write_multiple_files_batch_and_security(monkeypatch, tmp_path):
    """
    Zero-Debt Test: Ensures write_multiple_files batches correctly,
    saves tokens, and strictly obeys the Blood-Brain Barrier.
    """
    # 1. Sandbox the environment
    monkeypatch.setattr("System.tools.file_system.ROOT_DIR", tmp_path)

    # ⚡ SHIFT-LEFT: Mock the sandbox boundary to prevent import-time cache leakage
    def mock_is_safe_path(target_path):
        return "Studio" in target_path.parts

    monkeypatch.setattr("System.tools.file_system.is_safe_path", mock_is_safe_path)

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()

    # 2. Provide a batch payload
    files_payload = [
        {"filepath": "Studio/App.jsx", "content": "export default App;"},
        {"filepath": "Studio/index.css", "content": "body { color: black; }"},
        {
            "filepath": "System/core/hacked.py",
            "content": "print('hacked')",
        },  # Malicious!
    ]

    # 3. Execute the batch tool
    result = write_multiple_files(files_payload)

    # 4. Strict Validation
    assert (studio_dir / "App.jsx").exists()
    assert (studio_dir / "index.css").exists()
    assert (studio_dir / "App.jsx").read_text(encoding="utf-8") == "export default App;"

    # Malicious file MUST be blocked
    hacked_file = tmp_path / "System" / "core" / "hacked.py"
    assert not hacked_file.exists(), (
        "Blood-Brain Barrier failed to block malicious batch write!"
    )

    assert "Successfully wrote: Studio/App.jsx" in result
    assert "SECURITY BLOCK" in result


def test_motor_cortex_background_proprioception(mocker):
    """
    Zero-Debt Test: Ensures manage_background_process correctly targets the unified
    Proprioceptive background subsystem and triggers execution tracking accurately.
    """
    # 1. Mock the unified proprioceptive management handler instead of execution internals
    mock_proprio = mocker.patch(
        "System.neuroanatomy.autonomic.proprioception.manage_background_process",
        return_value="SUCCESS: Process started and verified bound to port 3000.",
    )

    # 2. Fire execution parameters through the Motor Cortex tool bridge
    result = manage_background_process(
        action="start",
        command="npm run dev",
        port=3000,
        cwd_path="Studio/Brain-Website",
    )

    # 3. Strict Validation: Ensure validation pipelines pass cleanly through the bridge
    assert "SUCCESS" in result
    mock_proprio.assert_called_once_with(
        action="start",
        name="",
        command="npm run dev",
        cwd="Studio/Brain-Website",
        port=3000,
    )


def test_diagnostic_vital_compilation(monkeypatch, tmp_path):
    """
    Zero-Debt Test: Verifies that get_system_vitals dynamically tracks
    metabolic costs and intercepts historical immune interventions.
    """
    from rich.console import Console

    monkeypatch.setattr("System.tools.diagnostic.ROOT_DIR", tmp_path)
    monkeypatch.setenv("BRAIN_OS_HEADLESS", "1")

    # 1. Setup a dummy ledger tracking a successful microglia response and token metadata
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "agent_interactions.jsonl"

    log_file.write_text(
        '{"response": "Microglia Successfully Healed the System.", "tokens": {"total_tokens": 12500}}\n'
        '{"response": "Normal response.", "tokens": {"total_tokens": 5000}}\n',
        encoding="utf-8",
    )

    # 2. Setup an engram file
    engram_dir = tmp_path / "Meta" / "Engrams"
    engram_dir.mkdir(parents=True)
    (engram_dir / "test_reflex.json").write_text("{}", encoding="utf-8")

    # 3. Compile Vitals Panel
    panel = get_system_vitals()

    # 4. Strict Validation using Rich's native capture engine
    console = Console(width=150)  # Provide ample width to prevent text wrapping
    with console.capture() as capture:
        console.print(panel)

    full_telemetry_dump = capture.get()

    # 5. Assertions
    assert "REM Sleep Mode" in full_telemetry_dump
    assert "1 active Engrams" in full_telemetry_dump
    assert "1 successful cellular healings" in full_telemetry_dump
    assert "17,500 tokens burned" in full_telemetry_dump
