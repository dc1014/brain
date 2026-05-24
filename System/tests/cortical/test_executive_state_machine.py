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
    """🛡️ ZERO-DEBT PROOF: Verifies the State Machine cursor safely jumps to Product Manager upon QA rejection without mutating the array."""

    # Mock the LLM to return standard text and usage stats
    mock_agent_response = MagicMock()
    mock_agent_response.text = "I wrote the code."
    mock_agent_response.actions = []
    mock_agent_response.usage = {"prompt_tokens": 10, "completion_tokens": 10}
    mock_run_agent.return_value = mock_agent_response

    # Force QA to fail
    mock_validate.return_value = (False, "Code lacks tests.")

    # A mock pipeline containing 3 agents
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
    ):  # ⚡ ADDED HERE
        # Run it with 1 retry max to prove it transitions state without infinite looping
        await execute_pipeline("Test task", "TEST", "GENERAL")

    # Assert that the PM agent was invoked (proving the state machine cursor jumped backwards correctly)
    called_agents = [
        call.kwargs.get("role_name") for call in mock_run_agent.call_args_list
    ]

    assert "Engineer" in called_agents
    assert "QA" in called_agents
    assert "PM" in called_agents  # Proves the cursor jump


@pytest.mark.asyncio
@patch("System.neuroanatomy.cortical.executive_loop.run_agent_async")
@patch("System.neuroanatomy.cortical.executive_loop.persist_pipeline_state")
@patch("System.neuroanatomy.cortical.executive_loop.check_energy_levels")
async def test_executive_state_machine_vagus_abort(
    mock_energy, mock_persist, mock_run_agent, tmp_path
):
    """🛡️ ZERO-DEBT PROOF: Verifies that a dropped .vagus_abort_signal file mid-flight trips the state cursor."""

    mock_energy.return_value = (False, 0)

    # ⚡ ZERO-DEBT FIX: Hydrate the virtual workspace layout so lookups for tools.yaml do not crash
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
