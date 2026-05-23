# --- System/tests/core/test_onboarding_synapses.py ---
import os
import pytest
from System.core.onboarding.synapses import verify_api_key


# --- System/tests/core/onboarding/test_onboarding_synapses.py ---


@pytest.mark.asyncio
async def test_verify_api_key_fails_regex_instantly(mocker):
    """Proves that a malformed key is rejected without ever firing a network request."""
    # ⚡ FIX: Patch litellm directly
    mock_acompletion = mocker.patch("litellm.acompletion")

    result = await verify_api_key("ANTHROPIC", "bad_key", "anthropic/claude-3-5-haiku")
    assert not result
    mock_acompletion.assert_not_called()


@pytest.mark.asyncio
async def test_verify_api_key_network_success(mocker):
    """Proves that a valid key that passes the 1-token ping returns True."""
    # ⚡ FIX: Patch litellm directly
    mock_acompletion = mocker.patch("litellm.acompletion")

    valid_key = "sk-" + ("A" * 48)
    result = await verify_api_key("OPENAI", valid_key, "openai/gpt-4o-mini")

    assert result
    mock_acompletion.assert_called_once()
    assert os.environ.get("OPENAI_API_KEY") != valid_key


@pytest.mark.asyncio
async def test_verify_api_key_network_failure(mocker):
    """Proves that a valid regex key with an empty quota returns False."""
    # ⚡ FIX: Patch litellm directly
    mock_acompletion = mocker.patch("litellm.acompletion")
    mock_acompletion.side_effect = Exception("429 Insufficient Quota")

    valid_key = "AIzaSy" + ("B" * 33)
    result = await verify_api_key("GEMINI", valid_key, "gemini/gemini-2.5-flash")

    assert not result
    assert os.environ.get("GEMINI_API_KEY") != valid_key
