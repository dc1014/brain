# --- System/tests/test_tools.py ---
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
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
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
    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch(
        "System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Professional"}
    )

    write_result = write_safe_file("System/malicious.py", "print('hacked')")
    assert "SECURITY BLOCK" in write_result

    read_result = read_safe_file(".env")
    assert "SECURITY BLOCK" in read_result

    list_result = list_safe_directory("System")

    assert (
        "ERROR: Directory not found" in list_result or "SECURITY BLOCK" in list_result
    )


def test_bootstrap_security_block(tmp_path: Path, mocker) -> None:  # type: ignore
    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    result = bootstrap_project("../../malicious_project")
    assert "SECURITY BLOCK" in result


def test_execute_command_security_and_hitl(tmp_path: Path, mocker) -> None:  # type: ignore
    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})
    mocker.patch.dict("os.environ", {"BRAIN_OS_HEADLESS": "0"}, clear=True)

    studio_dir = tmp_path / "Studio" / "TestProject"
    studio_dir.mkdir(parents=True, exist_ok=True)

    block_result = execute_command(["ls"], "../../")
    assert "PATH TRAVERSAL BLOCKED" in block_result


@patch("System.neuroanatomy.peripheral.motor.log_metabolism")
def test_adr_safety_blocks(mock_log, mocker) -> None:
    from System.tools import rename_safe_file, write_safe_file

    mocker.patch("System.tools.file_system.is_safe_path", return_value=True)

    write_res = write_safe_file("Studio/Project/docs/adr/001-test.md", "data")
    assert "SECURITY BLOCK" in write_res

    append_res = append_safe_file("Studio/Project/docs/adr/001-test.md", "data")
    assert "SECURITY BLOCK" in append_res

    rename_res_1 = rename_safe_file(
        "Studio/Project/docs/adr/001-test.md", "Studio/Project/new.md"
    )
    assert "SECURITY BLOCK" in rename_res_1
    assert "Cannot modify, move, or create ADRs" in rename_res_1

    rename_res_2 = rename_safe_file(
        "Studio/Project/old.md", "Studio/Project/docs/adr/002-test.md"
    )
    assert "SECURITY BLOCK" in rename_res_2


def test_copy_safe_file_security(tmp_path: Path, mocker) -> None:  # type: ignore
    from System.tools import copy_safe_file

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch(
        "System.tools.sandbox.ALLOWED_DIRECTORIES",
        {tmp_path / "Media", tmp_path / "Studio"},
    )

    media_dir = tmp_path / "Media"
    media_dir.mkdir()
    source_file = media_dir / "logo.png"
    source_file.write_text("dummy binary data")

    result = copy_safe_file("Media/logo.png", "Studio/logo.png")
    assert "SUCCESS" in result
    assert (tmp_path / "Studio/logo.png").exists()

    block_result = copy_safe_file("Media/logo.png", "../../Windows/System32/hacked.png")
    assert "SECURITY BLOCK" in block_result

    adr_dir = tmp_path / "Studio" / "adr"
    adr_dir.mkdir(parents=True)
    adr_file = adr_dir / "001-architecture.md"
    adr_file.write_text("secret architecture")

    adr_block = copy_safe_file("Studio/adr/001-architecture.md", "Studio/stolen.md")
    assert "SECURITY BLOCK: Cannot copy ADRs." in adr_block


def test_search_safe_directory_security_and_metrics(tmp_path: Path, mocker) -> None:  # type: ignore
    from System.tools import search_safe_directory

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch(
        "System.tools.sandbox.ALLOWED_DIRECTORIES",
        {tmp_path / "Studio", tmp_path / "Professional"},
    )

    studio_dir = tmp_path / "Studio" / "Project"
    studio_dir.mkdir(parents=True)

    target_file = studio_dir / "marketing.md"
    target_file.write_text("The Open-Core model is our primary strategy.")

    node_modules = studio_dir / "node_modules"
    node_modules.mkdir()
    ignored_file = node_modules / "docs.md"
    ignored_file.write_text("Open-Core")

    result = search_safe_directory("Open-Core", "Studio/Project")
    assert "marketing.md" in result
    assert "node_modules" not in result
    assert "[Telemetry: Scanned" in result

    block_result = search_safe_directory("password", "../../Windows")
    assert "SECURITY BLOCK" in block_result


def test_analyze_safe_syntax(tmp_path: Path, mocker) -> None:  # type: ignore
    from System.tools import analyze_safe_syntax

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True)

    assert "SECURITY BLOCK" in analyze_safe_syntax("../../outside.py")
    assert "ERROR: File" in analyze_safe_syntax("Studio/missing.py")

    py_file = studio_dir / "test.py"
    py_file.write_text("print('hello')")

    mock_subprocess = mocker.patch("System.tools.execution.subprocess.run")

    mock_subprocess.return_value = mocker.MagicMock(returncode=0)
    assert "Linter passed" in analyze_safe_syntax("Studio/test.py")

    mock_subprocess.return_value = mocker.MagicMock(
        returncode=1, stdout="SyntaxError on line 1", stderr=""
    )
    result = analyze_safe_syntax("Studio/test.py")
    assert "Linter found errors" in result
    assert "SyntaxError" in result


def test_read_file_signatures_tool(tmp_path, mocker) -> None:  # type: ignore
    from System.tools import read_file_signatures

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sensory.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.forge.ROOT_DIR", tmp_path)

    mocker.patch("System.tools.sandbox.ALLOWED_DIRECTORIES", {tmp_path})

    test_file = tmp_path / "test_module.py"
    test_file.write_text("def mock_func():\n    print('heavy logic')", encoding="utf-8")

    block_result = read_file_signatures("../../test_module.py")
    assert "SECURITY BLOCK" in block_result

    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello", encoding="utf-8")
    txt_result = read_file_signatures("test.txt")
    assert "ERROR: AST stubbing currently only supports" in txt_result

    mocker.patch(
        "System.ast_parser.extract_signatures", return_value="def mock_func(): ..."
    )

    success_result = read_file_signatures("test_module.py")
    assert '<document_signatures path="test_module.py">' in success_result
    assert "def mock_func():" in success_result


def test_execute_command_headless_bypass(monkeypatch, tmp_path):
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

    monkeypatch.setattr(
        "builtins.input", lambda *args: pytest.fail("HITL prompt was not bypassed!")
    )

    result = execute_command(["python", "--version"], "Studio")

    assert "PATH TRAVERSAL BLOCKED" not in result
    assert "<shell_output>" in result


def test_sense_environment_tool(monkeypatch):
    from System.tools import sense_environment

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
        config = yaml.safe_load(f)

    tools = config.get("tools", {})

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
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
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
    from System.tools.execution import deploy_project
    from System.core.schemas import ExecutionResult

    mocker.patch("System.tools.file_system.ROOT_DIR", tmp_path)
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.neuroanatomy.systemic.blood_brain_barrier.ROOT_DIR", tmp_path)

    studio_dir = tmp_path / "Studio" / "WebProject"
    studio_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(studio_dir)),
    )

    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret", return_value=None
    )
    result_no_token = deploy_project(str(studio_dir))
    assert isinstance(result_no_token, ExecutionResult)
    assert not result_no_token.success
    assert "DEPLOYMENT_TOKEN missing" in result_no_token.output

    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret",
        return_value="fake_deployment_token",
    )
    mocker.patch.dict(
        "os.environ",
        {"BRAIN_OS_HEADLESS": "0", "BRAIN_EXECUTION_TIER": "1"},
        clear=True,
    )
    mocker.patch("builtins.input", return_value="n")

    result_denied = deploy_project(str(studio_dir))
    assert not result_denied.success
    assert "User explicitly denied" in result_denied.output

    mocker.patch("builtins.input", return_value="y")

    mocker.patch(
        "System.tools.sandbox.execute_in_sandbox",
        return_value=ExecutionResult(
            success=True,
            output="<deployment_success>\nSimulated deploy for WebProject\n</deployment_success>",
        ),
    )

    result_success = deploy_project(str(studio_dir), provider="custom")
    assert result_success.success
    assert "Simulated deploy" in result_success.output


def test_write_multiple_files_batch_and_security(monkeypatch, tmp_path):
    monkeypatch.setattr("System.tools.file_system.ROOT_DIR", tmp_path)

    def mock_is_safe_path(target_path):
        return "Studio" in target_path.parts

    monkeypatch.setattr("System.tools.file_system.is_safe_path", mock_is_safe_path)

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()

    files_payload = [
        {"filepath": "Studio/App.jsx", "content": "export default App;"},
        {"filepath": "Studio/index.css", "content": "body { color: black; }"},
        {
            "filepath": "System/core/hacked.py",
            "content": "print('hacked')",
        },
    ]

    result = write_multiple_files(files_payload)

    assert (studio_dir / "App.jsx").exists()
    assert (studio_dir / "index.css").exists()
    assert (studio_dir / "App.jsx").read_text(encoding="utf-8") == "export default App;"

    hacked_file = tmp_path / "System" / "core" / "hacked.py"
    assert not hacked_file.exists(), (
        "Blood-Brain Barrier failed to block malicious batch write!"
    )

    assert "Successfully wrote: Studio/App.jsx" in result
    assert "SECURITY BLOCK" in result


def test_motor_cortex_background_proprioception(mocker):
    mock_proprio = mocker.patch(
        "System.neuroanatomy.autonomic.proprioception.manage_background_process",
        return_value="SUCCESS: Process started and verified bound to port 3000.",
    )

    result = manage_background_process(
        action="start",
        command="npm run dev",
        port=3000,
        cwd_path="Studio/Brain-Website",
    )

    assert "SUCCESS" in result
    mock_proprio.assert_called_once_with(
        action="start",
        name="",
        command="npm run dev",
        cwd="Studio/Brain-Website",
        port=3000,
    )


def test_diagnostic_vital_compilation(monkeypatch, tmp_path):
    from rich.console import Console

    monkeypatch.setattr("System.tools.diagnostic.ROOT_DIR", tmp_path)
    monkeypatch.setenv("BRAIN_OS_HEADLESS", "1")

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "agent_interactions.jsonl"

    log_file.write_text(
        '{"response": "Microglia Successfully Healed the System.", "tokens": {"total_tokens": 12500}}\n'
        '{"response": "Normal response.", "tokens": {"total_tokens": 5000}}\n',
        encoding="utf-8",
    )

    engram_dir = tmp_path / "Meta" / "Engrams"
    engram_dir.mkdir(parents=True)
    (engram_dir / "test_reflex.json").write_text("{}", encoding="utf-8")

    panel = get_system_vitals()

    console = Console(width=150)
    with console.capture() as capture:
        console.print(panel)

    full_telemetry_dump = capture.get()

    assert "REM Sleep Mode" in full_telemetry_dump
    assert "1 active Engrams" in full_telemetry_dump
    assert "1 successful cellular healings" in full_telemetry_dump
    assert "17,500 tokens burned" in full_telemetry_dump
