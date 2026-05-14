import os
import builtins
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
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.completion", return_value=MockResponse()
    )


@pytest.fixture(autouse=True)
def block_test_logging(monkeypatch):
    """
    Intercepts any attempt to write to the production log file during tests
    and securely redirects it into the void (os.devnull).
    """
    original_open = builtins.open

    def safe_open(file, *args, **kwargs):
        file_path = str(file).lower()
        # Block the production log, but ALLOW temporary test logs!
        if "agent_interactions.jsonl" in file_path and "pytest" not in file_path:
            return original_open(os.devnull, *args, **kwargs)
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", safe_open)
