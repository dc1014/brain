import os
import builtins
import pytest
import socket


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
    Intercepts any attempt to write to the production log files during tests
    and securely redirects it into the void (os.devnull).
    """
    original_open = builtins.open

    def safe_open(file, *args, **kwargs):
        file_path = str(file).lower()
        # 🛡️ ARCHITECTURAL SILENCING: Intercept both interactions AND autobiography logs during test execution frame
        is_prod_log = (
            "agent_interactions.jsonl" in file_path
            or "autobiography.jsonl" in file_path
        )

        if is_prod_log and "pytest" not in file_path:
            return original_open(os.devnull, *args, **kwargs)
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", safe_open)


@pytest.fixture(autouse=True)
def autonomic_sandbox(tmp_path, monkeypatch):
    """
    SHIFT-LEFT: This fixture runs automatically before EVERY test.
    It brutally intercepts any attempt by the OS to access the physical ROOT_DIR
    and redirects it to an ephemeral tmp_path, guaranteeing 0 side effects.
    """
    modules_with_root_dir = [
        "System.core.paths",
        "System.tools.sandbox",
        "System.tools.file_system",
        "System.tools.execution",
        "System.tools.sensory",
        "System.tools.cognitive",
        "System.tools.forge",
        "System.neuroanatomy.systemic.blood_brain_barrier",
        "System.neuroanatomy.cortical.occipital",
        "System.neuroanatomy.sensory.somatosensory",
        "System.neuroanatomy.sensory.gustatory",
        "System.neuroanatomy.sensory.olfactory",
    ]

    for mod in modules_with_root_dir:
        try:
            monkeypatch.setattr(f"{mod}.ROOT_DIR", tmp_path)
        except (AttributeError, ImportError):
            pass  # Module might not have imported it, perfectly fine


@pytest.fixture(autouse=True)
def protect_host_os(monkeypatch):
    """
    🛡️ SHIFT-LEFT SECURITY: Globally disables os.system during Pytest.
    Ensures that no test (especially the Vestibular system) can ever accidentally
    execute 'git checkout' or 'rm -rf' on the host machine.
    """
    monkeypatch.setattr("os.system", lambda cmd: None)


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    """Blocks all tests from making live network calls. Fails instantly if they try."""

    def stunted_getaddrinfo(*args, **kwargs):
        raise RuntimeError(
            "🚨 A test tried to hit the live internet! You are missing an LLM mock."
        )

    monkeypatch.setattr(socket, "getaddrinfo", stunted_getaddrinfo)


@pytest.fixture(autouse=True)
def enforce_strict_offline_testing(monkeypatch):
    """
    🛡️ ZERO-DEBT ACCELERATION SHIELD
    Forces all unit tests to execute strictly in-memory.
    If a test attempts to hit the live internet due to a missing LLM patch,
    it fails instantly in 1ms rather than hanging for minutes.
    """

    def block_network_egress(*args, **kwargs):
        raise RuntimeError(
            "🚨 CRITICAL COGNITIVE LEAK: A test tried to access the live internet! "
            "You are missing an LLM mock or patch for this execution frame."
        )

    monkeypatch.setattr(socket, "getaddrinfo", block_network_egress)
