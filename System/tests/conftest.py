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
