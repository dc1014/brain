import os
import builtins
import pytest
import socket
import psutil
from unittest.mock import patch
from System.tools.microsandbox import cleanup_worker_pool
from System.neuroanatomy.autonomic.medulla import cleanup_active_medullas


@pytest.fixture(autouse=True, scope="session")
def setup_testing_environment():
    """Enforces a self-defending environment variable barrier across the test session."""
    os.environ["BRAIN_OS_TESTING"] = "1"
    os.environ["BRAIN_OS_HEADLESS"] = "1"

    # 🔐 TESTING REALIGNMENT SHIELD: Globally enable code execution for the test suite scope
    # so containment matrix and guillotine checks can execute. Specific opt-in unit tests
    # explicitly clear or mock this to 'false' to evaluate read-only boundaries.
    os.environ["BRAIN_ENABLE_CODE_EXECUTION"] = "true"
    yield


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


@pytest.fixture(autouse=True)
def guard_autonomic_daydreams(request):
    """
    🛡️ Subcortex Isolation Guard: Automatically disables background DMN daydreams
    for all side-effect daemon tests (like Medulla/Thalamus shutdowns) unless
    the suite explicitly targets test_dmn.py.
    """
    # If the active running test file is explicitly test_dmn.py, allow full execution
    if "test_dmn" in request.module.__name__:
        yield
    else:
        # For all other tests, mock trigger_daydreams out to prevent loop hangs
        with patch(
            "System.neuroanatomy.autonomic.dmn.trigger_daydreams"
        ) as mock_trigger:
            mock_trigger.return_value = (
                "Daydream bypassed safely inside side-effect daemon test context."
            )
            yield


@pytest.fixture(autouse=True)
def guard_and_clean_autonomic_subcortex(request, tmp_path):
    """
    🛡️ Global Kernel Process Tree Reaper: Disables background DMN daydreams,
    scaffolds mock system configurations for specific tests, and sweeps processes.
    """
    # ⚡ SCAFFOLDING CONTAINMENT GATE: Scaffold config only for specific tool/cortical tracks
    # to protect core DNA and onboarding engines from FileExistsError collisions.
    if request.module and any(
        mod in request.module.__name__
        for mod in [
            "test_mirror_neurons",
            "test_sandbox",
            "test_read_only_sandbox",
            "test_sandbox_containment",
        ]
    ):
        config_dir = tmp_path / "System" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        fingerprint_file = config_dir / "stylistic_fingerprint.json"
        if not fingerprint_file.exists():
            fingerprint_file.write_text("{}", encoding="utf-8")

    if request.module and "test_dmn" in request.module.__name__:
        yield
    else:
        with patch(
            "System.neuroanatomy.autonomic.dmn.trigger_daydreams"
        ) as mock_trigger:
            mock_trigger.return_value = (
                "Bypassed safely inside daemon side-effect context."
            )
            yield

    # Synchronously clear memory reference loops
    cleanup_worker_pool()
    cleanup_active_medullas()

    # ⚡ KERNEL PROCESS REAPER: Query the host operating system to kill escaping child process contexts
    try:
        current_process = psutil.Process(os.getpid())
        for child in current_process.children(recursive=True):
            if child.name().lower() in [
                "deno",
                "deno.exe",
                "python",
                "python.exe",
                "cmd.exe",
                "bash",
            ]:
                try:
                    child.kill()
                except Exception:
                    pass
    except Exception:
        pass


@pytest.fixture
def safe_subprocess_mock(mocker):
    """
    🛡️ SHIFT-LEFT MOCKING: Prevents AsyncMock from swallowing synchronous
    subprocess methods (.close, .kill) which causes test hangs and coroutine leaks.
    Inject this into any test that needs to fake an asyncio subprocess.
    """
    from unittest.mock import AsyncMock, MagicMock

    # 1. Create the base async mock (THIS WAS MISSING!)
    mock_proc = AsyncMock()

    mock_proc.stdout = AsyncMock()
    mock_proc.stdout.at_eof = MagicMock(return_value=False)

    # ⚡ Simulate Deno emitting the cryptographic success signal
    mock_proc.stdout.readline = AsyncMock(
        side_effect=[
            b"User-space V8 sandbox verified.\n",
            b"[__EXECUTION_COMPLETE__]\n",
            b"",
        ]
    )

    # 2. Force the synchronous properties to be normal MagicMocks
    mock_proc.stdin = AsyncMock()
    mock_proc.stdin.close = MagicMock()  # Sync!
    mock_proc.stdin.write = MagicMock()  # Sync!
    mock_proc.terminate = MagicMock()  # Sync!
    mock_proc.kill = MagicMock()  # Sync!

    # 3. Explicitly define async methods
    mock_proc.wait = AsyncMock()
    mock_proc.communicate = AsyncMock()
    mock_proc.stdin.wait_closed = AsyncMock()
    mock_proc.stdin.drain = AsyncMock()

    # 4. Globally patch the asyncio execution for the duration of the test
    mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

    return mock_proc
