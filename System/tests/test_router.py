from unittest.mock import MagicMock
from System.router import run_agent, analyze_task, trigger_synaptic_plugin


def test_run_agent_success(mocker) -> None:  # type: ignore
    """Test that the agent correctly extracts the text from a successful API response."""
    mock_completion = mocker.patch("System.router.completion")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mocked AI response."
    mock_response.choices[0].message.tool_calls = None
    mock_completion.return_value = mock_response

    result = run_agent("Worker (Claude)", "test-model", "system", "user")

    assert result.text == "This is a mocked AI response."
    assert result.actions == []


def test_run_agent_error_handling(mocker) -> None:  # type: ignore
    """Test that the agent gracefully catches and returns API errors."""
    mocker.patch("System.router.log_interaction")
    mock_completion = mocker.patch("System.router.completion")
    mock_completion.side_effect = Exception("Simulated API Error")

    result = run_agent("Worker (Claude)", "test-model", "system", "user")

    assert result.text == "Error: Simulated API Error"
    assert result.actions == []


def test_analyze_task_deterministic_blocks() -> None:
    """Test that shift-left heuristic checks block illegal prompts before hitting the LLM."""

    # 1. Test the delete block
    is_valid, reason, route, domain, _ = analyze_task("Can you delete my journal?")
    assert is_valid is False
    assert "delete tool" in reason
    assert route == "NONE"

    # 2. Test the system boundary block
    is_valid, reason, route, domain, _ = analyze_task("Read the system/tools.py file.")
    assert is_valid is False
    assert "sandboxed" in reason.lower()
    assert route == "NONE"


def test_synaptic_plugin_missing(mocker) -> None:  # type: ignore
    """Test that the engine gracefully falls back when the Pro plugin is missing."""
    # Directly patch the 'exists' method to simulate the missing plugin
    mocker.patch("System.router.Path.exists", return_value=False)

    success = trigger_synaptic_plugin("STUDIO", ["Fact 1"])
    assert success is False  # Should return False to trigger Markdown fallback


def test_synaptic_plugin_installed(mocker) -> None:  # type: ignore
    """Test that the engine routes to the GPU when the Pro plugin is installed."""
    # Directly patch the 'exists' method to simulate the installed plugin
    mocker.patch("System.router.Path.exists", return_value=True)

    success = trigger_synaptic_plugin("STUDIO", ["Fact 1"])
    assert success is True  # Should return True to skip Markdown
