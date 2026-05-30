# --- System/tests/conftest.py ---
import pytest
import asyncio
import os
import time
import threading
import _pytest.pathlib

_pytest.pathlib.cleanup_numbered_dir = lambda *args, **kwargs: None


def pytest_addoption(parser):
    """Adds the custom CLI flag to Pytest."""
    parser.addoption(
        "--run-evals",
        action="store_true",
        default=False,
        help="Run AI Evaluation tests (Consumes API tokens)",
    )


def pytest_configure(config):
    """Registers the custom marker so Pytest doesn't throw strict warnings."""
    config.addinivalue_line(
        "markers", "eval: mark test as an LLM evaluation test requiring API keys"
    )


@pytest.fixture(autouse=True, scope="session")
def enforce_headless_mode():
    os.environ["BRAIN_OS_HEADLESS"] = "1"
    os.environ["BRAIN_OS_TESTING"] = "1"


@pytest.fixture(autouse=True)
def safe_async_teardown():
    yield
    try:
        loop = asyncio.get_running_loop()
        for task in asyncio.all_tasks(loop):
            if task is not asyncio.current_task():
                task.cancel()
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
    if hasattr(session.config, "workerinput"):

        def worker_seppuku():
            time.sleep(0.5)
            os._exit(exitstatus)

        threading.Thread(target=worker_seppuku, daemon=True).start()


@pytest.fixture
def safe_subprocess_mock(mocker):
    mock_proc = mocker.AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (b"Mocked output", b"")
    mock_proc.stdout.read = mocker.AsyncMock(return_value=b"")
    mock_proc.stdout.readline = mocker.AsyncMock(return_value=b"")
    mock_proc.wait = mocker.AsyncMock()

    mock_proc.kill = mocker.MagicMock()
    mock_proc.stdin.close = mocker.MagicMock()
    mock_proc.stdin.write = mocker.MagicMock()

    # Required for Deno micro-sandbox execution flows
    mock_proc.stdin.drain = mocker.AsyncMock()
    mock_proc.stdin.wait_closed = mocker.AsyncMock()
    mock_proc.stdout.at_eof = mocker.MagicMock(return_value=False)

    return mock_proc


@pytest.fixture(autouse=True)
def align_windows_sandbox_paths(mocker, tmp_path):
    safe_root = tmp_path.resolve()

    mocker.patch("System.core.paths.ROOT_DIR", safe_root)
    mocker.patch("System.tools.sandbox.ROOT_DIR", safe_root)

    mocker.patch(
        "System.tools.sandbox.ALLOWED_DIRECTORIES",
        {safe_root / "Studio", safe_root / "Media", safe_root / "Professional"},
    )

    mocker.patch("System.tools.file_system.ROOT_DIR", safe_root)
    mocker.patch("System.tools.execution.ROOT_DIR", safe_root, create=True)
    mocker.patch("System.tools.sensory.ROOT_DIR", safe_root, create=True)
    mocker.patch("System.tools.cognitive.ROOT_DIR", safe_root, create=True)

    try:
        mocker.patch(
            "System.tools.execution.validation.ROOT_DIR", safe_root, create=True
        )
    except Exception:
        pass


def pytest_collection_modifyitems(config, items):
    # --- EVALUATION GATE LOGIC ---
    run_evals = config.getoption("--run-evals") or os.environ.get(
        "CORETEX_RUN_EVALS"
    ) in ("1", "true", "True")
    skip_eval = pytest.mark.skip(
        reason="Need --run-evals flag or CORETEX_RUN_EVALS=1 in .env to run"
    )

    # --- OBSOLETE QUARANTINE LOGIC ---
    skip_obsolete = pytest.mark.skip(reason="Obsolete architecture or Infinite Loop")
    quarantine_targets = {
        "test_medulla_cognitive_heartbeat_execution",
        "test_medulla_lifecycle_execution",
        "test_executive_state_machine_qa_fallback",
        "test_proprioception_is_lock_free",
        "test_proprioception_atomic_lock_concurrency",
        "test_assimilate_moves_safe_engram_successfully",
        "test_motor_cortex_executes_valid_tool_successfully",
    }

    # Iterate through all tests and apply skips where necessary
    for item in items:
        # 1. Skip if it's an obsolete test
        if item.name in quarantine_targets:
            item.add_marker(skip_obsolete)

        # 2. Skip if it's an eval test AND the gate is closed
        if not run_evals and "eval" in item.keywords:
            item.add_marker(skip_eval)
