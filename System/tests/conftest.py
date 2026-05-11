import pytest


@pytest.fixture(autouse=True)
def no_human_input_in_tests(monkeypatch):
    """
    Shift-Left Test Defense:
    If a test accidentally triggers a human-in-the-loop prompt (like Broca failing
    a mock and asking for a retry), this instantly auto-aborts it instead of
    hanging the entire test suite forever.
    """
    monkeypatch.setattr("builtins.input", lambda prompt: "n")


@pytest.fixture(autouse=True)
def bypass_amygdala_network_calls(mocker):
    """
    Globally mocks the Amygdala's LLM network call across the entire test suite.
    This prevents tests from 'Failing Closed' due to missing API keys in the CI/test environment.
    """

    class MockMessage:
        content = "SAFE"

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    # Intercept the network call and instantly return "SAFE" for all tests automatically
    mocker.patch("System.organs.amygdala.completion", return_value=MockResponse())
