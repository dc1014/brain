from unittest.mock import MagicMock
from System.runtime import analyze_task


def test_analyze_task_deterministic_blocks() -> None:
    """Test that shift-left heuristics block illegal prompts before hitting the LLM."""

    # 1. Test the destructive action block
    is_valid, reason, route, domain, _ = analyze_task("Can you delete my journal?")
    assert is_valid is False
    assert "delete tool" in reason.lower()
    assert route == "NONE"

    # 2. Test the system boundary block
    is_valid, reason, route, domain, _ = analyze_task("Read the system/cli.py file.")
    assert is_valid is False
    assert "sandboxed" in reason.lower()
    assert route == "NONE"


def test_analyze_task_llm_parsing(mocker) -> None:  # type: ignore
    """Test that the dispatcher correctly extracts ROUTE and DOMAIN from the LLM."""
    mock_completion = mocker.patch("System.runtime.completion")

    # Setup mock LLM response returning the exact format we demand
    msg = MagicMock()
    msg.content = "ROUTE: READ_ONLY\nDOMAIN: STUDIO"

    mock_response = MagicMock(choices=[MagicMock(message=msg)])
    # Mock the usage stats to prove token counting works
    mock_response.usage = MagicMock(
        prompt_tokens=10, completion_tokens=5, total_tokens=15
    )
    mock_completion.return_value = mock_response

    is_valid, reason, route, domain, usage = analyze_task("Search the Studio folder")

    assert is_valid is True
    assert route == "READ_ONLY"
    assert domain == "STUDIO"
    assert usage["total_tokens"] == 15


def test_analyze_task_llm_rejection(mocker) -> None:  # type: ignore
    """Test that the dispatcher correctly handles explicit REJECTED messages."""
    mock_completion = mocker.patch("System.runtime.completion")

    # Setup mock LLM response acting like it hit a limitation
    msg = MagicMock()
    msg.content = "REJECTED: I cannot browse the live internet."
    mock_completion.return_value = MagicMock(choices=[MagicMock(message=msg)])

    is_valid, reason, route, domain, _ = analyze_task(
        "Go to google.com and find the news."
    )

    assert is_valid is False
    # SHIFT-LEFT FIX: Account for the uppercase transformation in runtime.py
    assert "browse the live internet" in reason.lower()
    assert route == "NONE"


def test_analyze_task_api_error(mocker) -> None:  # type: ignore
    """Test that API errors during dispatch fail safely."""
    mock_completion = mocker.patch("System.runtime.completion")
    mock_completion.side_effect = Exception("Anthropic API is down.")

    is_valid, reason, route, domain, _ = analyze_task("Build me a website.")

    assert is_valid is False
    assert "Dispatcher API Error" in reason
    assert "Anthropic API is down" in reason
    assert route == "NONE"
