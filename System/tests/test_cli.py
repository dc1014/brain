# --- System/tests/test_cli.py ---
from unittest.mock import MagicMock
from System.llm import run_agent_async
import asyncio
import typer
from typer.testing import CliRunner
import json
import pytest
import System.cli as cli_module
from System.cli import app

runner = CliRunner()


def test_run_agent_success(mocker) -> None:
    mock_completion = mocker.patch("System.llm.acompletion")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mocked AI response."
    mock_response.choices[0].message.tool_calls = None

    async def mock_acompletion(*args, **kwargs):
        return mock_response

    mock_completion.side_effect = mock_acompletion
    result = asyncio.run(
        run_agent_async("Worker (Claude)", "test-model", "system", "user")
    )
    assert result.text == "This is a mocked AI response."
    assert result.actions == []


def test_run_agent_error_handling(mocker) -> None:
    mock_completion = mocker.patch("System.llm.acompletion")

    async def mock_acompletion_error(*args, **kwargs):
        raise Exception("Simulated API Error")

    mock_completion.side_effect = mock_acompletion_error
    result = asyncio.run(
        run_agent_async("Worker (Claude)", "test-model", "system", "user")
    )
    assert "API/Execution Error" in result.text


def test_run_os_retry_circuit_breaker(mocker, monkeypatch) -> None:
    monkeypatch.delenv("BRAIN_OS_HEADLESS", raising=False)
    monkeypatch.setenv("BRAIN_OS_BYPASS_PFC", "1")

    mocker.patch(
        "System.core.orchestrator.route_sensory_input",
        return_value=(True, "Approved", "FORGE", "STUDIO", {"total_tokens": 10}),
    )

    mocker.patch(
        "System.neuroanatomy.cortical.executive_loop.get_dna_config",
        return_value={
            "routes": {"FORGE": [{"agent": "qa_auditor"}]},
            "agents": {
                "product_manager": {
                    "name": "PM",
                    "model": "mock",
                    "system_prompt": "",
                    "creates_milestone": True,
                },
                "qa_auditor": {
                    "name": "QA",
                    "model": "mock",
                    "system_prompt": "",
                    "creates_milestone": False,
                },
            },
            "models": {"mock": "mock"},
        },
    )

    from System.llm import AgentResponse

    agent_calls = []

    async def mock_run_agent_side_effect(*args, **kwargs):
        role_name = str(
            kwargs.get("role_name", args[0] if len(args) > 0 else "")
        ).lower()
        agent_calls.append(role_name)
        if "qa" in role_name:
            return AgentResponse(
                text='{"audit_result": "FAIL", "reasoning": "Bad."}',
                usage={"total_tokens": 50},
            )
        return AgentResponse(
            text="Here is the generated code.", usage={"total_tokens": 50}
        )

    mocker.patch(
        "System.neuroanatomy.cortical.executive_loop.run_agent_async",
        side_effect=mock_run_agent_side_effect,
    )
    mocker.patch("builtins.input", side_effect=["y", "n", "n", "n"])

    from System.cli import task

    task("FORGE TASK: Test retry circuit breaker", obsidian=False)
    assert any("qa" in agent for agent in agent_calls)


def test_interrupted_queue_interception(monkeypatch, tmp_path, mocker):
    monkeypatch.setattr("System.cli.ROOT_DIR", tmp_path)
    queue_file = tmp_path / "System" / "execution_queue.json"
    queue_file.parent.mkdir(parents=True, exist_ok=True)

    mock_queue = {
        "original_task": "Build a react app",
        "route_type": "WORKSPACE",
        "domain": "STUDIO",
        "remaining_steps": [{"agent": "product_manager"}],
    }
    queue_file.write_text(json.dumps(mock_queue), encoding="utf-8")
    monkeypatch.setenv("BRAIN_OS_HEADLESS", "1")

    mocker.patch(
        "System.neuroanatomy.cortical.executive_loop.execute_pipeline",
        new_callable=mocker.AsyncMock,
    )
    mocker.patch("System.core.boot.bootstrap", return_value=True)

    from System.cli import main

    with pytest.raises(typer.Exit):
        main()


def test_destroy_aborts_on_no(mocker, monkeypatch) -> None:
    monkeypatch.delenv("BRAIN_OS_HEADLESS", raising=False)
    mocker.patch("System.cli.Confirm.ask", return_value=False)

    result = runner.invoke(app, ["destroy"])
    assert "Apoptosis aborted" in result.stdout
    assert result.exit_code == 0


def test_destroy_executes_on_yes(mocker, monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("BRAIN_OS_HEADLESS", raising=False)
    mocker.patch.object(cli_module, "ROOT_DIR", tmp_path)
    mocker.patch("System.cli.Confirm.ask", return_value=True)

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "agent_interactions.jsonl").touch()

    env_file = tmp_path / ".env"
    env_file.touch()

    sys_dir = tmp_path / "System"
    sys_dir.mkdir(parents=True, exist_ok=True)
    queue_file = sys_dir / "execution_queue.json"
    queue_file.touch()

    result = runner.invoke(app, ["destroy"])
    assert "Systemic Apoptosis complete" in result.stdout
    assert not log_dir.exists()
    assert not env_file.exists()
    assert not queue_file.exists()
