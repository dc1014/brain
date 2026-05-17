import pytest
from unittest.mock import MagicMock
from System.neuroanatomy.limbic.thalamus import filter_attention, route_sensory_input


# --- FILTER ATTENTION TESTS (Preserved) ---


def test_thalamus_fast_path():
    """Proves the Thalamus skips filtering if the memory is short enough."""
    short_memory = "This is a short memory."
    filtered = filter_attention("Build a react app", short_memory)

    # Should return exactly the original text (bypassing the LLM)
    assert filtered == short_memory


def test_thalamus_filtering(monkeypatch):
    """Proves the Thalamus correctly calls the LLM for large memories."""

    # Create a dummy memory large enough to trigger the Thalamus (> 2000 chars)
    large_memory = "A" * 2500

    # Mock the LLM to return a specific filtered string
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.thalamus.completion",  # ⚡ ZERO-DEBT: Patch the local module reference!
        lambda *args, **kwargs: type(
            "Mock",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "message": type(
                                "Msg", (), {"content": "Filtered React bullet point."}
                            )()
                        },
                    )()
                ]
            },
        )(),
    )

    filtered = filter_attention("Build a react app", large_memory)
    assert "Filtered React bullet point." in filtered


# --- ROUTE SENSORY INPUT TESTS (Upgraded from analyze_task) ---


@pytest.mark.asyncio
async def test_thalamus_pydantic_fallback(mocker, monkeypatch):
    """Proves the Thalamus gracefully catches malformed JSON from the LLM."""

    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction", return_value=None
    )
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.scan_prompt", return_value=(True, "Safe")
    )

    async def mock_acompletion(*args, **kwargs):
        class MockMessage:
            content = "This is completely invalid JSON that will break Pydantic."

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]
            usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        return MockResponse()

    # ⚡ ZERO-DEBT: Patch the LLM call inside the new Thalamus module
    monkeypatch.setattr("System.llm.acompletion", mock_acompletion)

    # 2. Execute the Thalamus using the new function name
    is_valid, reason, route, domain, usage = await route_sensory_input(
        "Write some code."
    )

    # 3. Assert the Pydantic ValidationError was caught and handled gracefully
    assert route == "UNKNOWN"
    assert domain == "NONE"


@pytest.mark.asyncio
async def test_thalamus_rejection_logic(mocker, monkeypatch):
    """Proves the Thalamus correctly rejects tasks outside OS capabilities."""

    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction", return_value=None
    )
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.scan_prompt", return_value=(True, "Safe")
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

    monkeypatch.setattr("System.llm.acompletion", mock_acompletion)

    is_valid, reason, route, domain, usage = await route_sensory_input("Order a pizza")

    assert is_valid is False
    # ⚡ ZERO-DEBT: Match the Thalamus's .upper() capitalization shift
    assert "I CANNOT ORDER A PHYSICAL PIZZA FOR YOU." in reason


@pytest.mark.asyncio
async def test_thalamus_amygdala_interception(mocker):
    """Proves the Thalamus blocks prompts if the Amygdala detects a threat."""
    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction", return_value=None
    )
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.scan_prompt",
        return_value=(False, "Threat Detected"),
    )

    is_safe, reason, route, domain, usage = await route_sensory_input("destroy the OS")

    assert is_safe is False
    assert reason == "Threat Detected"
    assert route == "NONE"


@pytest.mark.asyncio
async def test_thalamus_gut_reaction_shortcut(mocker):
    """Proves the Thalamus bypasses the LLM entirely if the Enteric nervous system has a reflex."""
    mock_gut_response = (
        True,
        "Gut Approved",
        "WORKSPACE",
        "STUDIO",
        {"total_tokens": 0},
    )
    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction",
        return_value=mock_gut_response,
    )

    is_safe, reason, route, domain, usage = await route_sensory_input(
        "build a react app"
    )

    assert is_safe is True
    assert route == "WORKSPACE"
    assert reason == "Gut Approved"
