from unittest.mock import MagicMock
from pathlib import Path

from System.llm import run_agent
from System.runtime import analyze_task
from System.cli import app, init
from System.tools import bootstrap_project, execute_command
from typer.testing import CliRunner

runner = CliRunner()


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

    # 1. Test the destructive action block
    is_valid, reason, route, domain, _ = analyze_task("Can you delete my journal?")
    assert is_valid is False
    assert "amygdala rule" in reason.lower()

    # 2. Test the vital organ protection
    is_valid, reason, route, domain, _ = analyze_task("Can you read the .env file?")
    assert is_valid is False
    assert "amygdala boundary" in reason.lower()


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
    mocker.patch("System.organs.blood_brain_barrier.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.ALLOWED_DIRECTORIES", {tmp_path / "Studio"})

    # <-- ADD THIS LINE: Bypass the LLM network call in the test environment
    mocker.patch("System.organs.amygdala.scan_command", return_value=(True, "Safe"))

    studio_dir = tmp_path / "Studio" / "TestProject"
    studio_dir.mkdir(parents=True, exist_ok=True)

    # 1. Test Security Boundary
    block_result = execute_command("ls", "../../")
    assert "PATH TRAVERSAL BLOCKED" in block_result

    # 2. Test HITL Strict Rejection
    mocker.patch("builtins.input", return_value="n")
    mocker.patch.dict("os.environ", {"BRAIN_OS_HEADLESS": "0"}, clear=True)

    # Pass the exact path so subprocess finds the temp directory
    deny_result = execute_command("ls", str(studio_dir))
    assert "SECURITY BLOCK: User explicitly denied" in deny_result

    # 3. Test Execution Approval (Standard 'y')
    mocker.patch("builtins.input", return_value="y")

    # If your test_cli.py imports execute_command from System.tools, use:
    mock_subprocess = mocker.patch("System.tools.subprocess.run")

    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "mock_ls_output"
    mock_subprocess.return_value.stderr = ""

    # FIX: Pass the absolute path variable, just like in Step 2!
    approve_result = execute_command("ls", str(studio_dir))

    # FIX: Assert the restored XML data contract
    assert "<shell_output>" in approve_result
    assert "mock_ls_output" in approve_result


def test_run_os_retry_circuit_breaker(mocker, monkeypatch) -> None:  # type: ignore
    """Test that the pipeline immediately aborts if user denies autonomous retry."""

    # 0. Clear test state contamination
    monkeypatch.delenv("BRAIN_OS_HEADLESS", raising=False)

    mocker.patch(
        "System.cli.analyze_task",
        return_value=(True, "Approved", "FORGE", "STUDIO", {"total_tokens": 10}),
    )

    from System.llm import AgentResponse

    agent_calls = []

    def mock_run_agent_side_effect(*args, **kwargs):
        role_name = str(
            kwargs.get("role_name", args[0] if len(args) > 0 else "")
        ).lower()
        agent_calls.append(role_name)

        if "auditor" in role_name:
            # Include BOTH legacy and modern fail flags to guarantee the circuit breaker trips
            return AgentResponse(
                text="[FAIL]\n<audit_result>FAIL</audit_result>",
                usage={"total_tokens": 50},
            )
        return AgentResponse(
            text="Here is the generated code.", usage={"total_tokens": 50}
        )

    mocker.patch("System.runtime.run_agent", side_effect=mock_run_agent_side_effect)

    # Supply 'y' to authorize pipeline, 'n' to deny the retry.
    mocker.patch("builtins.input", side_effect=["y", "n", "n", "n"])

    # Catch edge cases where rich.prompt is used instead of builtins.input
    try:
        mocker.patch("rich.prompt.Prompt.ask", return_value="n")
        mocker.patch("rich.prompt.Confirm.ask", return_value=False)
    except Exception:
        pass

    from System.cli import task

    task("FORGE TASK: Test retry circuit breaker", obsidian=False)

    # ZERO-DEBT ASSERTIONS: Test the mathematical outcome, not the print statements.
    assert any("auditor" in agent for agent in agent_calls), (
        "QA Auditor was never reached."
    )
    assert not any("deployment" in agent for agent in agent_calls), (
        "Circuit breaker failed: Deployment Ops was called after a denied retry!"
    )


def test_init_autonomous_git_hooks(mocker, tmp_path) -> None:  # type: ignore
    """Ensure the init command automatically discovers repositories and wires up git hooks."""
    from System.cli import init

    # 1. Point Brain OS's root directory to our isolated test sandbox
    cli_path = tmp_path / "System" / "cli.py"
    cli_path.parent.mkdir(parents=True)
    mocker.patch("System.cli.__file__", str(cli_path))

    # 2. Build a fake repository structure that matches Forge
    fake_repo = tmp_path / "Studio" / "FakeForge"
    (fake_repo / ".git").mkdir(parents=True)

    fake_hooks_dir = fake_repo / "scripts" / "githooks"
    fake_hooks_dir.mkdir(parents=True)
    (fake_hooks_dir / "pre-commit").touch()

    # 3. Intercept subprocess to prevent actual git commands from running
    mock_subprocess = mocker.patch("System.cli.subprocess.run")
    mock_print = mocker.patch("System.cli.console.print")

    # 4. Run the initialization sequence
    init()

    # 5. Assertions
    assert mock_subprocess.call_count == 2

    # Check that Git Config was called correctly
    call_1_args, call_1_kwargs = mock_subprocess.call_args_list[0]
    assert call_1_args[0] == ["git", "config", "core.hooksPath", "scripts/githooks"]
    assert call_1_kwargs["cwd"] == fake_repo

    # Check that the chmod executable command was called
    call_2_args, call_2_kwargs = mock_subprocess.call_args_list[1]
    assert call_2_args[0] == [
        "git",
        "update-index",
        "--chmod=+x",
        "scripts/githooks/pre-commit",
    ]
    assert call_2_kwargs["cwd"] == fake_repo

    # Verify the user is notified
    printed_texts = [
        str(call.args[0]) for call in mock_print.call_args_list if call.args
    ]
    assert any("Secured Git hooks for repository" in text for text in printed_texts)
    assert any("FakeForge" in text for text in printed_texts)


def test_task_obsidian_flag(tmp_path, monkeypatch):
    """Test that the --obsidian flag safely queues the task and exits."""
    from typer.testing import CliRunner

    runner = CliRunner()

    def mock_analyze(*args):
        return True, "Mock reason", "Forge", "Studio", {"tokens": 0}

    monkeypatch.setattr("System.cli.analyze_task", mock_analyze)

    # 1. Setup exact mock directory structure
    system_dir = tmp_path / "System"
    system_dir.mkdir(parents=True, exist_ok=True)
    mock_cli_file = system_dir / "cli.py"

    # 2. Monkeypatch the module's __file__ directly (Not Path)
    monkeypatch.setattr("System.cli.__file__", str(mock_cli_file))

    # 3. Run the Typer command
    result = runner.invoke(app, ["task", "Build a test app", "--obsidian"])

    assert result.exit_code == 0
    assert "Task safely queued" in result.stdout

    # 4. Test that the file was actually created with the right content
    mock_pending_file = system_dir / "Pending_Actions.md"
    assert mock_pending_file.exists()

    file_contents = mock_pending_file.read_text(encoding="utf-8")
    assert "Pending Task: Forge" in file_contents
    assert "Build a test app" in file_contents


def test_execute_pending(tmp_path, monkeypatch):
    """Test that execute_pending reads the file, runs tasks, and clears the queue."""
    from typer.testing import CliRunner

    runner = CliRunner()

    # 1. Setup exact mock directory structure
    system_dir = tmp_path / "System"
    system_dir.mkdir(parents=True, exist_ok=True)
    mock_cli_file = system_dir / "cli.py"

    monkeypatch.setattr("System.cli.__file__", str(mock_cli_file))

    # 2. Create the mock pending file
    mock_pending_file = system_dir / "Pending_Actions.md"
    mock_pending_file.write_text(
        "### ⏳ Pending Task: Forge\n**Prompt:** Refactor the UI\n---\n",
        encoding="utf-8",
    )

    # 3. Mock the LLM and Execution functions
    monkeypatch.setattr(
        "System.cli.analyze_task", lambda x: (True, "Valid", "Forge", "Studio", {})
    )
    monkeypatch.setattr("System.cli.execute_pipeline", lambda d, r, dom: None)

    # 4. Run the command
    result = runner.invoke(app, ["execute-pending"])

    # 5. Assertions
    assert result.exit_code == 0
    assert "Found 1 pending tasks" in result.stdout
    assert "Executing Task 1/1" in result.stdout

    # Ensure the file was wiped clean after execution
    assert "*Queue is currently empty.*" in mock_pending_file.read_text(
        encoding="utf-8"
    )


def test_forage_command(monkeypatch, capsys):
    """Proves the forage command executes the correct pipeline in headless mode."""
    from System.cli import app
    from typer.testing import CliRunner
    import os

    runner = CliRunner()

    # Mock the pipeline execution
    executed_args = {}

    def mock_execute_pipeline(desc, route, domain):
        executed_args["desc"] = desc
        executed_args["route"] = route
        executed_args["domain"] = domain

    monkeypatch.setattr("System.cli.execute_pipeline", mock_execute_pipeline)

    result = runner.invoke(app, ["forage", "https://example.com", "--domain", "STUDIO"])

    assert result.exit_code == 0
    assert executed_args["route"] == "SUBCONSCIOUS_FORAGE"
    assert executed_args["domain"] == "STUDIO"
    assert "https://example.com" in executed_args["desc"]
    assert os.environ.get("BRAIN_OS_HEADLESS") == "1"


def test_daydream_command(monkeypatch, capsys):
    """Proves the daydream command executes the correct pipeline in headless mode."""
    from System.cli import app
    from typer.testing import CliRunner
    import os

    runner = CliRunner()

    # Mock the pipeline execution
    executed_args = {}

    def mock_execute_pipeline(desc, route, domain):
        executed_args["desc"] = desc
        executed_args["route"] = route
        executed_args["domain"] = domain

    monkeypatch.setattr("System.cli.execute_pipeline", mock_execute_pipeline)

    result = runner.invoke(app, ["daydream", "--domain", "PROFESSIONAL"])

    assert result.exit_code == 0
    assert executed_args["route"] == "SUBCONSCIOUS_DAYDREAM"
    assert executed_args["domain"] == "PROFESSIONAL"
    assert os.environ.get("BRAIN_OS_HEADLESS") == "1"


def test_evolve_command(monkeypatch, tmp_path):
    """Proves the evolve command safely merges staging mutations and creates backups."""
    from System.cli import evolve

    root = tmp_path
    monkeypatch.setattr("System.cli.ROOT_DIR", root)

    # Setup paths (Meta Domain)
    mutations = root / "Meta" / "Mutations.md"
    mutations.parent.mkdir(parents=True)
    mutations.write_text(
        '<neuroplasticity agent="dispatcher">New Rule</neuroplasticity>',
        encoding="utf-8",
    )

    config_dir = root / "System" / "config"
    config_dir.mkdir(parents=True)
    agents_file = config_dir / "agents.yaml"
    agents_file.write_text(
        "agents:\n  dispatcher:\n    system_prompt: 'Base prompt.'\n", encoding="utf-8"
    )

    # Execute
    evolve()

    # Assert Backup Created
    assert (config_dir / "agents.yaml.bak").exists(), "Safety backup was not created!"

    # Assert DNA Modified
    updated_dna = agents_file.read_text(encoding="utf-8")
    assert "<neuroplastic_rule" in updated_dna, "DNA was not modified!"
    assert "New Rule" in updated_dna, "The specific mutation was not injected!"

    # Assert Staging Cleared
    assert "New Rule" not in mutations.read_text(encoding="utf-8"), (
        "Staging area was not cleared after evolution!"
    )
