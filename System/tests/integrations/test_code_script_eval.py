import pytest

from System.neuroanatomy.limbic.thalamus import route_sensory_input
from System.llm import run_agent_async
from System.core.dna import get_dna_config
from System.neuroanatomy.cortical.executive_loop import execute_pipeline

# ==============================================================================
# LIVE LLM EVALUATIONS (Requires `pytest -m eval`)
# ==============================================================================


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_thalamus_routes_scripts_to_code_script():
    """
    EVALUATION: Proves the Thalamus correctly identifies single-file scripts
    and routes them to CODE_SCRIPT instead of the bloated CODE_BACKEND route.
    """
    prompt = "write a python script in the root of the Studio folder named potato.py that outputs spudman!"
    is_valid, reason, route, domain, usage = await route_sensory_input(prompt)

    assert is_valid is True, "Thalamus incorrectly blocked the prompt."
    assert route == "CODE_SCRIPT", (
        f"Expected CODE_SCRIPT to catch simple scripts, but got {route}"
    )
    assert domain == "STUDIO", f"Expected STUDIO domain, got {domain}"


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_qa_auditor_uses_audit_pass_tag():
    """
    EVALUATION: Proves the QA Auditor follows the new system prompt and outputs
    the strict <AUDIT_PASS> tag instead of just saying 'PASS' in plain text.
    """
    cfg = get_dna_config()["agents"]["qa_auditor"]

    # Simulate the working memory context of a successful script creation
    user_context = (
        "WORKING MEMORY:\n"
        "- Solo Hacker executed write_safe_file to create Studio/potato.py\n"
        "- Content of Studio/potato.py is `print('spudman')`\n\n"
        "CURRENT TASK: Audit the file."
    )

    response = await run_agent_async(
        role_name="QA Auditor",
        model_string=cfg.get("model", "gemini/gemini-2.5-flash"),
        system_prompt=cfg["system_prompt"],
        user_prompt=user_context,
        route="CODE_SCRIPT",
        domain="STUDIO",
        tools=None,  # No tools needed for this specific text-check eval
    )

    assert "<AUDIT_PASS>" in response.text.upper(), (
        f"QA Auditor failed to include <AUDIT_PASS> tag. Output: {response.text}"
    )


# ==============================================================================
# OFFLINE ORCHESTRATION TESTS (Runs automatically to prevent infinite loops)
# ==============================================================================


@pytest.mark.asyncio
async def test_executive_loop_terminates_on_audit_pass(mocker, tmp_path):
    """
    UNIT: Proves the while-loop in executive_loop.py correctly parses <AUDIT_PASS>
    and exits cleanly without infinitely looping or triggering retries.
    """
    mocker.patch("System.neuroanatomy.cortical.executive_loop.ROOT_DIR", tmp_path)
    mocker.patch("System.neuroanatomy.cortical.executive_loop.persist_pipeline_state")
    mocker.patch("System.neuroanatomy.cortical.executive_loop.clear_pipeline_state")
    mocker.patch("System.neuroanatomy.cortical.executive_loop.commit_transaction")
    mocker.patch("System.neuroanatomy.cortical.executive_loop.restore_balance")

    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    mocker.patch(
        "System.core.orchestrator.route_sensory_input",
        return_value=(True, "Approved", "CODE_SCRIPT", "STUDIO", {}),
    )

    # Mock the configuration to only load the Solo Hacker and QA Auditor
    mocker.patch(
        "System.neuroanatomy.cortical.executive_loop.get_dna_config",
        return_value={
            "routes": {
                "CODE_SCRIPT": [{"agent": "solo_engineer"}, {"agent": "qa_auditor"}]
            },
            "agents": {
                "solo_engineer": {
                    "name": "Solo Hacker",
                    "model": "mock",
                    "system_prompt": "",
                    "creates_milestone": True,
                },
                "qa_auditor": {
                    "name": "QA Auditor",
                    "model": "mock",
                    "system_prompt": "",
                    "creates_milestone": False,
                },
            },
            "models": {"mock": "mock"},
            "tools": {},
        },
    )

    # Mock the LLM to instantly output a success tag during the QA phase
    class MockResponse:
        def __init__(self, text):
            self.text = text
            self.actions = []
            self.usage = {}

    async def mock_run_agent(*args, **kwargs):
        role_name = kwargs.get("role_name", "")
        if "QA" in role_name:
            return MockResponse("The script looks perfect. <AUDIT_PASS>")
        return MockResponse("I wrote the script.")

    mock_llm = mocker.patch(
        "System.neuroanatomy.cortical.executive_loop.run_agent_async",
        side_effect=mock_run_agent,
    )

    # Run the pipeline
    await execute_pipeline("Make a script", "CODE_SCRIPT", "STUDIO")

    # If the loop bug still existed, this test would hang forever.
    # If it completes, we just ensure it called both agents exactly once.
    assert mock_llm.call_count == 2, (
        "Pipeline did not execute exactly two agents (Solo Hacker + QA Auditor)"
    )
