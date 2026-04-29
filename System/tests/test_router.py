from unittest.mock import MagicMock
from System.router import run_agent


def test_run_agent_success(mocker):
    """Test that the agent correctly extracts the text from a successful API response."""
    # Intercept the litellm 'completion' function inside router.py
    mock_completion = mocker.patch("System.router.completion")

    # Create a fake response object that perfectly mimics what Claude/Gemini returns
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mocked AI response."
    mock_completion.return_value = mock_response

    # Execute our function
    result = run_agent("Worker (Claude)", "test-model", "system", "user")

    # Verify the logic processed the fake response correctly
    assert result == "This is a mocked AI response."
    mock_completion.assert_called_once()


def test_run_agent_error_handling(mocker):
    """Test that the agent gracefully catches and returns API errors."""
    mock_completion = mocker.patch("System.router.completion")

    # Force the API to throw a simulated timeout or quota error
    mock_completion.side_effect = Exception("Simulated API Error")

    # Execute our function
    result = run_agent("Worker (Claude)", "test-model", "system", "user")

    # Verify the try/except block caught it
    assert result == "Error: Simulated API Error"
