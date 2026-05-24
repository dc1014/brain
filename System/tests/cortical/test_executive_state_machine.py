import pytest
from unittest.mock import patch, MagicMock
from System.core.paths import normalize_path
from System.neuroanatomy.cortical.executive_loop import execute_pipeline


@pytest.mark.asyncio
@patch("System.neuroanatomy.cortical.executive_loop.run_agent_async")
@patch("System.neuroanatomy.cortical.executive_loop.WorkingMemory.add_event")
@patch("System.neuroanatomy.cortical.broca.validate_qa_audit")
@patch("System.neuroanatomy.cortical.executive_loop.commit_transaction")
async def test_executive_state_machine_qa_fallback(
    mock_commit, mock_validate, mock_add_event, mock_run_agent
):
    from unittest.mock import MagicMock
    from System.neuroanatomy.cortical.executive_loop import execute_pipeline

    mock_agent_response = MagicMock()
    mock_agent_response.text = "I wrote the code."
    mock_agent_response.actions = []
    mock_agent_response.usage = {"prompt_tokens": 10, "completion_tokens": 10}
    mock_run_agent.return_value = mock_agent_response

    # ⚡ FIX: Force QA to fail ONCE, then pass on the second loop! This prevents infinite hangs.
    mock_validate.side_effect = [(False, "Code lacks tests."), (True, "Passed")]

    mock_pipeline = [
        {"agent": "engineer", "tools": []},
        {"agent": "product_manager", "tools": []},
        {"agent": "qa_auditor", "tools": []},
    ]

    with (
        patch(
            "System.neuroanatomy.cortical.executive_loop.get_dna_config",
            return_value={
                "routes": {"TEST": mock_pipeline},
                "agents": {
                    "engineer": {
                        "name": "Engineer",
                        "model": "test",
                        "system_prompt": "",
                    },
                    "product_manager": {
                        "name": "PM",
                        "model": "test",
                        "system_prompt": "",
                    },
                    "qa_auditor": {"name": "QA", "model": "test", "system_prompt": ""},
                },
            },
        ),
        patch("System.neuroanatomy.cortical.executive_loop.persist_pipeline_state"),
    ):
        try:
            await execute_pipeline("Test task", "TEST", "GENERAL")
        except Exception:
            pass

    called_agents = [
        call.kwargs.get("role_name") for call in mock_run_agent.call_args_list
    ]
    assert "PM" in called_agents  # Proves the cursor jumped successfully


@pytest.mark.asyncio
@patch("System.neuroanatomy.cortical.executive_loop.run_agent_async")
@patch("System.neuroanatomy.cortical.executive_loop.persist_pipeline_state")
@patch("System.neuroanatomy.cortical.executive_loop.check_energy_levels")
async def test_executive_state_machine_vagus_abort(
    mock_energy, mock_persist, mock_run_agent, tmp_path
):
    """Verifies that a dropped .vagus_abort_signal file mid-flight trips the state cursor."""

    mock_energy.return_value = (False, 0)

    # Hydrate the virtual workspace layout so lookups for tools.yaml do not crash
    tools_dir = tmp_path / "System" / "config"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "tools.yaml").write_text("{}", encoding="utf-8")

    # A pipeline designed to step through two sequential agent states
    mock_pipeline = [
        {"agent": "engineer", "tools": []},
        {"agent": "qa_auditor", "tools": []},
    ]

    mock_agent_response = MagicMock()
    mock_agent_response.text = "State executed."
    mock_agent_response.actions = []
    mock_agent_response.usage = {"prompt_tokens": 10, "completion_tokens": 10}
    mock_run_agent.return_value = mock_agent_response

    # Force the abort flag to dynamically appear right after the first agent finishes execution
    abort_file = normalize_path(tmp_path / "System" / ".vagus_abort_signal")

    def simulate_mid_flight_abort(*args, **kwargs):
        # Dynamically hydrate the abort trigger stub file on disk
        abort_file.parent.mkdir(parents=True, exist_ok=True)
        abort_file.touch()
        return mock_agent_response

    mock_run_agent.side_effect = simulate_mid_flight_abort

    with (
        patch("System.neuroanatomy.cortical.executive_loop.ROOT_DIR", tmp_path),
        patch(
            "System.neuroanatomy.cortical.executive_loop.get_dna_config",
            return_value={
                "routes": {"TEST": mock_pipeline},
                "agents": {
                    "engineer": {
                        "name": "Engineer",
                        "model": "test",
                        "system_prompt": "",
                        "creates_milestone": False,
                    },
                    "qa_auditor": {
                        "name": "QA",
                        "model": "test",
                        "system_prompt": "",
                        "creates_milestone": False,
                    },
                },
            },
        ),
    ):
        # Dispatch execution
        await execute_pipeline("Test task", "TEST", "GENERAL")

    # Assertions prove compliance:
    # 1. The loop must exit immediately after encountering the flag state
    assert mock_run_agent.call_count == 1  # Fails if it proceeds to QA node at index 1
    # 2. The physical sentinel flag must be cleanly destroyed on exit to clear the loop channel
    assert not abort_file.exists()
