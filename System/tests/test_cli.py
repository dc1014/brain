from unittest.mock import MagicMock
from pathlib import Path

from System.llm import run_agent
from System.runtime import analyze_task
from System.cli import init
from System.tools import bootstrap_project, execute_command


def test_run_agent_success(mocker) -> None:  # type: ignore
    """Test that the agent correctly extracts the text from a successful API response."""
    # CHANGED: Mock System.llm instead of System.router
    mock_completion = mocker.patch("System.llm.completion")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mocked AI response."
    mock_response.choices[0].message.tool_calls = None
    mock_completion.return_value = mock_response

    result = run_agent("Worker (Claude)", "test-model", "system", "user")

    assert result.text == "This is a mocked AI response."
    assert result.actions == []


def test_run_agent_error_handling(mocker) -> None:  # type: ignore
    """Test that the agent gracefully catches and returns API errors."""
    # CHANGED: Mock System.llm instead of System.router
    mocker.patch("System.llm.log_interaction")
    mock_completion = mocker.patch("System.llm.completion")
    mock_completion.side_effect = Exception("Simulated API Error")

    result = run_agent("Worker (Claude)", "test-model", "system", "user")

    assert result.text == "API/Execution Error: Simulated API Error"
    assert result.actions == []


def test_analyze_task_deterministic_blocks() -> None:
    """Test that shift-left heuristic checks block illegal prompts before hitting the LLM."""

    # 1. Test the delete block
    is_valid, reason, route, domain, _ = analyze_task("Can you delete my journal?")
    assert is_valid is False
    assert "delete tool" in reason.lower()
    assert route == "NONE"

    # 2. Test the system boundary block
    is_valid, reason, route, domain, _ = analyze_task("Read the system/tools.py file.")
    assert is_valid is False
    assert "sandboxed" in reason.lower()
    assert route == "NONE"


def test_init_command_creates_vault(tmp_path, mocker) -> None:  # type: ignore
    """Test that the init command successfully builds the vault directories and foundational files."""

    # 1. Mock the root_dir dynamically so it targets our safe pytest temp directory
    mock_path_instance = MagicMock()
    mock_path_instance.parent.parent = tmp_path
    mocker.patch("System.cli.Path", return_value=mock_path_instance)

    # 2. Create a dummy .env.example in the temp directory so the copy logic can be tested
    dummy_env = tmp_path / ".env.example"
    dummy_env.write_text("MOCK_KEY=123")

    # 3. Execute the initialization
    init()

    # 4. Verify Directories were created
    assert (tmp_path / "Personal").exists()
    assert (tmp_path / "Professional").exists()
    assert (tmp_path / "Studio").exists()
    assert (tmp_path / "Meta").exists()
    assert (tmp_path / "logs").exists()

    # 5. Verify Foundational Files were created
    assert (tmp_path / "Meta/global-memory.md").exists()
    assert (tmp_path / "Studio/studio-memory.md").exists()

    # 6. Verify .env was successfully copied from the template
    assert (tmp_path / ".env").exists()
    assert (tmp_path / ".env").read_text() == "MOCK_KEY=123"


def test_bootstrap_security_block(tmp_path: Path, mocker) -> None:  # type: ignore
    """Test that projects cannot be bootstrapped outside allowed zones."""
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    # Try to clone into the root directory directly
    result = bootstrap_project("../../malicious_project")
    assert "SECURITY BLOCK" in result


def test_execute_command_security_and_hitl(tmp_path: Path, mocker) -> None:  # type: ignore
    """Test that command execution is sandboxed and respects HITL."""
    mocker.patch("System.tools.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    studio_dir = tmp_path / "Studio" / "TestProject"
    studio_dir.mkdir(parents=True)

    # 1. Test Security Boundary
    block_result = execute_command("ls", "../../")
    assert "SECURITY BLOCK" in block_result

    # 2. Test HITL Strict Rejection (Standard 'n' or unrecognized input)
    mocker.patch("builtins.input", return_value="n")
    deny_result = execute_command("ls", "Studio/TestProject")
    assert "SECURITY BLOCK: User explicitly denied" in deny_result

    # 3. Test Execution Approval (Standard 'y')
    mocker.patch("builtins.input", return_value="y")
    mock_subprocess = mocker.patch("System.tools.subprocess.run")
    mock_subprocess.return_value.returncode = 0
    approve_result = execute_command("ls", "Studio/TestProject")
    assert "SUCCESS" in approve_result
    mock_subprocess.assert_called_once()


def test_run_os_retry_circuit_breaker(mocker) -> None:  # type: ignore
    """Test that the pipeline immediately aborts if user denies autonomous retry."""

    # 1. Update: Mock analyze_task exactly where it is used in the CLI
    mocker.patch(
        "System.cli.analyze_task",
        return_value=(True, "Approved", "FORGE", "STUDIO", {"total_tokens": 10}),
    )

    from System.llm import AgentResponse

    def mock_run_agent_side_effect(*args, **kwargs):
        role_name = kwargs.get("role_name", args[0] if len(args) > 0 else "")
        if "Auditor" in role_name:
            return AgentResponse(
                text="[GRADE: FAIL] The code has hallucinations.",
                usage={"total_tokens": 50},
            )
        return AgentResponse(
            text="Here is the generated code.", usage={"total_tokens": 50}
        )

    # 2. Update: Mock run_agent in runtime
    mocker.patch("System.runtime.run_agent", side_effect=mock_run_agent_side_effect)

    mocker.patch("builtins.input", side_effect=["y", "n"])

    # 3. Update: Spy on console.print in runtime
    mock_print = mocker.patch("System.runtime.console.print")

    # 4. Update: Call task from cli
    from System.cli import task

    task("FORGE TASK: Test retry circuit breaker")

    abort_called = any(
        "User declined autonomous retry" in str(call.args[0])
        for call in mock_print.call_args_list
        if call.args
    )
    assert abort_called, (
        "The retry circuit breaker did not trigger the abort print statement."
    )


def test_sleep_command_observability(mocker, tmp_path) -> None:  # type: ignore
    """Ensure the sleep command successfully parses memories, calculates token weight, and prints observability metrics."""
    from System.cli import sleep
    from unittest.mock import MagicMock

    # 1. Setup mock log file
    log_file = tmp_path / "agent_interactions.jsonl"
    log_file.write_text('{"fake": "log data"}')
    mocker.patch("System.cli.LOG_FILE", log_file)
    mocker.patch("System.cli.LOG_DIR", tmp_path)

    # 2. Mock LLM to return a predictable JSON memory structure
    mock_completion = mocker.patch("System.cli.completion")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[
        0
    ].message.content = '{"STUDIO": ["Brain OS now supports Token Truncation. This saves money.", "Added a search tool."]}'
    mock_completion.return_value = mock_response

    # 3. Bypass config reading and file writing
    mocker.patch(
        "System.cli.yaml.safe_load",
        return_value={"domains": {"STUDIO": "Studio/studio-memory.md"}},
    )
    mock_append = mocker.patch("System.cli.append_safe_file", return_value="SUCCESS")
    mock_print = mocker.patch("System.cli.console.print")

    # Run the sleep cycle
    sleep()

    # Assertions
    mock_append.assert_called_once()
    appended_text = mock_append.call_args[0][1]
    assert "- Brain OS now supports Token Truncation." in appended_text

    # Verify the exact terminal output format
    printed_texts = [
        str(call.args[0]) for call in mock_print.call_args_list if call.args
    ]

    # Check that the Domain Header was printed
    assert any("STUDIO MEMORY UPDATED" in text for text in printed_texts)

    # Check that the First Sentence truncation and Token Cost math worked
    # "Brain OS now supports Token Truncation. This saves money." -> 57 chars // 4 = 14 tokens
    assert any(
        "└─ Brain OS now supports Token Truncation." in text and "~14 tokens" in text
        for text in printed_texts
    )
