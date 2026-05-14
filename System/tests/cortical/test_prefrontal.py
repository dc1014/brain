import os
from System.runtime import execute_pipeline


import pytest


@pytest.mark.asyncio
async def test_prefrontal_swarm_execution(mocker):
    # 1. Mock the API call to return immediately
    from System.llm import AgentResponse

    async def mock_run_agent(*args, **kwargs):
        return AgentResponse(
            text=f"Task complete by {kwargs.get('role_name')}",
            usage={"total_tokens": 100},
        )

    mocker.patch("System.runtime.run_agent_async", side_effect=mock_run_agent)
    mocker.patch("System.neuroanatomy.autonomic.vestibular.commit_transaction")
    mocker.patch("System.neuroanatomy.autonomic.vestibular.restore_balance")
    mocker.patch.dict(os.environ, {"BRAIN_OS_HEADLESS": "1"})

    # 2. Run the newly defined SWARM_FORGE pipeline
    try:
        await execute_pipeline("Build a fullstack app", "SWARM", "STUDIO")
        success = True
    except Exception as e:
        success = False
        print(f"Swarm failed: {e}")

    # 3. Assert it completed without thread collisions
    assert success is True
