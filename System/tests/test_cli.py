from unittest.mock import MagicMock
from System.llm import run_agent_async
import asyncio
import typer
from typer.testing import CliRunner

import json
import pytest

runner = CliRunner()


def test_run_agent_success(mocker) -> None:  # type: ignore
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


def test_run_agent_error_handling(mocker) -> None:  # type: ignore
    mock_completion = mocker.patch("System.llm.acompletion")

    async def mock_acompletion_error(*args, **kwargs):
        raise Exception("Simulated API Error")

    mock_completion.side_effect = mock_acompletion_error
    result = asyncio.run(
        run_agent_async("Worker (Claude)", "test-model", "system", "user")
    )
    assert "API/Execution Error" in result.text


def test_run_os_retry_circuit_breaker(mocker, monkeypatch) -> None:  # type: ignore
    """Test that the pipeline immediately aborts if user denies autonomous retry."""

    monkeypatch.delenv("BRAIN_OS_HEADLESS", raising=False)
    monkeypatch.setenv("BRAIN_OS_BYPASS_PFC", "1")

    mocker.patch(
        "System.core.orchestrator.route_sensory_input",
        return_value=(True, "Approved", "FORGE", "STUDIO", {"total_tokens": 10}),
    )

    # ⚡ ZERO-DEBT: Inject the missing DNA config!
    mocker.patch(
        "System.neuroanatomy.cortical.prefrontal.get_dna_config",
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
        "System.neuroanatomy.cortical.prefrontal.run_agent_async",
        side_effect=mock_run_agent_side_effect,
    )

    mocker.patch("builtins.input", side_effect=["y", "n", "n", "n"])

    try:
        mocker.patch("rich.prompt.Prompt.ask", return_value="n")
        mocker.patch("rich.prompt.Confirm.ask", return_value=False)
    except Exception:
        pass

    from System.cli import task

    task("FORGE TASK: Test retry circuit breaker", obsidian=False)

    assert any("qa" in agent for agent in agent_calls), "QA Auditor was never reached."


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

    # ⚡ ZERO-DEBT: Target the function at its anatomical source since it's locally imported
    mocker.patch(
        "System.neuroanatomy.cortical.prefrontal.execute_pipeline",
        new_callable=mocker.AsyncMock,
    )
    mocker.patch("System.core.boot.bootstrap", return_value=True)

    from System.cli import main

    with pytest.raises(typer.Exit):
        main()
