# --- System/tests/limbic/test_thalamus.py ---
import pytest
from unittest.mock import MagicMock
from System.neuroanatomy.limbic.thalamus import filter_attention, route_sensory_input


def test_thalamus_fast_path():
    short_memory = "This is a short memory."
    filtered = filter_attention("Build a react app", short_memory)
    assert filtered == short_memory


def test_thalamus_filtering(monkeypatch):
    large_memory = "A" * 2500

    monkeypatch.setattr(
        "System.neuroanatomy.limbic.thalamus.completion",
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


@pytest.mark.asyncio
async def test_thalamus_pydantic_fallback(mocker, monkeypatch):
    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction", return_value=None
    )
    mocker.patch("System.neuroanatomy.autonomic.interoception.log_metabolism")
    mocker.patch(
        "System.neuroanatomy.limbic.thalamus.scan_prompt", return_value=(True, "Safe")
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

    monkeypatch.setattr("System.llm.acompletion", mock_acompletion)

    is_valid, reason, route, domain, usage = await route_sensory_input(
        "Write some code."
    )

    assert is_valid is True
    assert route == "UNKNOWN"
    assert domain == "NONE"


@pytest.mark.asyncio
async def test_thalamus_rejection_logic(mocker, monkeypatch):
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
    assert "I CANNOT ORDER A PHYSICAL PIZZA FOR YOU." in reason


@pytest.mark.asyncio
async def test_thalamus_amygdala_interception(mocker):
    mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction", return_value=None
    )
    mocker.patch(
        "System.neuroanatomy.limbic.thalamus.scan_prompt",
        return_value=(False, "Threat Detected"),
    )

    is_safe, reason, route, domain, usage = await route_sensory_input("destroy the OS")

    assert is_safe is False
    assert reason == "Threat Detected"


@pytest.mark.asyncio
async def test_thalamus_gut_reaction_shortcut(mocker):
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
