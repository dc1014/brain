from unittest.mock import MagicMock
from System.router import run_agent, analyze_task


def test_run_agent_success(mocker) -> None:  # type: ignore
    """Test that the agent correctly extracts the text from a successful API response."""
    # Intercept the litellm 'completion' function inside router.py
    mock_completion = mocker.patch("System.router.completion")

    # Create a fake response object that mimics Claude/Gemini
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mocked AI response."

    # CRITICAL FIX: Explicitly set tool_calls to None so the ReAct loop breaks after 1 step
    mock_response.choices[0].message.tool_calls = None

    mock_completion.return_value = mock_response

    # Execute our function
    result = run_agent("Worker (Claude)", "test-model", "system", "user")

    # Verify the logic processed the fake response correctly using the new Dataclass properties
    assert result.text == "This is a mocked AI response."
    assert result.actions == []


def test_run_agent_error_handling(mocker) -> None:  # type: ignore
    """Test that the agent gracefully catches and returns API errors."""
    mocker.patch("System.router.log_interaction")
    mock_completion = mocker.patch("System.router.completion")

    # Force the API to throw a simulated timeout or quota error
    mock_completion.side_effect = Exception("Simulated API Error")

    # Execute our function
    result = run_agent("Worker (Claude)", "test-model", "system", "user")

    # Verify the try/except block caught it and returned the correct Dataclass structure
    assert result.text == "Error: Simulated API Error"
    assert result.actions == []


def test_analyze_task_deterministic_blocks() -> None:
    """Test that shift-left heuristic checks block illegal prompts before hitting the LLM."""

    # 1. Test the delete block
    is_valid, reason, route, _ = analyze_task("Can you delete my journal?")
    assert is_valid is False
    assert "delete tool" in reason
    assert route == "NONE"

    # 2. Test the system boundary block
    is_valid, reason, route, _ = analyze_task("Read the system/tools.py file.")
    assert is_valid is False
    assert "sandboxed" in reason
    assert route == "NONE"
