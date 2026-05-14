import pytest
import json
from unittest.mock import MagicMock
from System.runtime import analyze_task


@pytest.mark.asyncio
async def test_thalamus_pydantic_success(mocker, monkeypatch):
    """Proves the Thalamus correctly parses a valid Pydantic JSON schema."""

    # 1. Mock the Subconscious (Gut/Amygdala) to let the prompt pass
    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction", return_value=None
    )
    mocker.patch("System.neuroanatomy.systemic.enteric.save_gut_reaction")

    # 2. Mock a flawless LLM JSON output that matches the Pydantic Schema exactly
    valid_json = json.dumps(
        {
            "reasoning": "The user wants an image, routing to VISION.",
            "route": "VISION",
            "domain": "STUDIO",
        }
    )

    async def mock_acompletion(*args, **kwargs):
        class MockMessage:
            content = valid_json

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]
            usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        return MockResponse()

    monkeypatch.setattr("System.runtime.acompletion", mock_acompletion)

    # 3. Execute the Thalamus
    is_valid, reason, route, domain, usage = await analyze_task("Draw me a fox.")

    # 4. Assert mathematical accuracy and case-normalization
    assert is_valid is True
    assert route == "VISION"
    assert domain == "STUDIO"


@pytest.mark.asyncio
async def test_thalamus_pydantic_hallucination_catch(mocker, monkeypatch):
    """Proves the Thalamus intercepts missing keys and safely degrades instead of crashing."""

    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction", return_value=None
    )

    # 1. Mock a BAD LLM output (missing the 'reasoning' key required by Pydantic)
    bad_json = json.dumps({"route": "FORGE", "domain": "STUDIO"})

    async def mock_acompletion(*args, **kwargs):
        class MockMessage:
            content = bad_json

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]
            usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        return MockResponse()

    monkeypatch.setattr("System.runtime.acompletion", mock_acompletion)

    # 2. Execute the Thalamus
    is_valid, reason, route, domain, usage = await analyze_task("Write some code.")

    # 3. Assert the Pydantic ValidationError was caught and handled gracefully
    assert route == "UNKNOWN"
    assert domain == "NONE"


@pytest.mark.asyncio
async def test_thalamus_rejection_logic(mocker, monkeypatch):
    """Proves the Thalamus correctly rejects tasks outside OS capabilities."""

    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction", return_value=None
    )

    async def mock_acompletion(*args, **kwargs):
        class MockMessage:
            content = "REJECTED: I cannot order a physical pizza for you."

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]
            usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        return MockResponse()

    monkeypatch.setattr("System.runtime.acompletion", mock_acompletion)

    is_valid, reason, route, domain, usage = await analyze_task("Order me a pizza.")

    assert is_valid is False
    assert "I CANNOT ORDER A PHYSICAL PIZZA" in reason
