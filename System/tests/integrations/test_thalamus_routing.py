import pytest
from System.neuroanatomy.limbic.thalamus import route_sensory_input


@pytest.mark.eval
@pytest.mark.asyncio
async def test_eval_thalamus_routes_scripts_strictly_to_code_generation():
    """
    EVALUATION: Proves the Thalamus LLM obeys the agents.yaml constraints
    and refuses to route code/script creation to the WORKSPACE archivist.
    """
    prompt = "write a python script in the studio folder named hi.py that outputs hello world"

    is_valid, reason, route, domain, usage = await route_sensory_input(prompt)

    assert is_valid is True
    assert route == "CODE_GENERATION", (
        f"Expected CODE_GENERATION to catch scripts, but got {route}"
    )
    assert domain == "STUDIO", f"Expected STUDIO domain, got {domain}"
