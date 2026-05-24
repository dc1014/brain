import sys
from unittest.mock import patch
from System.core.concurrency import get_isolated_executor, lock_concurrency_defaults
from concurrent.futures import ProcessPoolExecutor


@patch("multiprocessing.set_start_method")
def test_lock_concurrency_defaults_unix(mock_set_start_method, monkeypatch):
    """Verifies forkserver is rigidly enforced on Unix systems."""
    monkeypatch.setattr(sys, "platform", "linux")
    lock_concurrency_defaults()
    mock_set_start_method.assert_called_once_with("forkserver")


@patch("multiprocessing.set_start_method")
def test_lock_concurrency_defaults_windows(mock_set_start_method, monkeypatch):
    """Verifies Windows gracefully ignores the Unix process lock."""
    monkeypatch.setattr(sys, "platform", "win32")
    lock_concurrency_defaults()
    mock_set_start_method.assert_not_called()


@patch(
    "multiprocessing.set_start_method",
    side_effect=RuntimeError("context has already been set"),
)
def test_lock_concurrency_defaults_idempotent(mock_set_start_method, monkeypatch):
    """Verifies the lock doesn't crash if called multiple times (e.g., during pytest loops)."""
    monkeypatch.setattr(sys, "platform", "darwin")
    # Should safely catch the RuntimeError and pass
    lock_concurrency_defaults()
    mock_set_start_method.assert_called_once()


def test_get_isolated_executor_legacy(monkeypatch):
    """Verifies fallback to ProcessPoolExecutor on <3.14."""
    monkeypatch.setattr(sys, "version_info", (3, 13, 0))
    executor = get_isolated_executor(max_workers=2)
    assert isinstance(executor, ProcessPoolExecutor)
    executor.shutdown()


def test_get_isolated_executor_314(monkeypatch):
    """Verifies PEP 734 Subinterpreter routing on 3.14+."""
    monkeypatch.setattr(sys, "version_info", (3, 14, 0))

    # Safely mock the 3.14 feature for the 3.12 test runner
    import concurrent.futures

    class MockInterpreterPoolExecutor:
        def __init__(self, max_workers):
            self.max_workers = max_workers

        def shutdown(self, wait=True, cancel_futures=False):
            pass

    monkeypatch.setattr(
        concurrent.futures,
        "InterpreterPoolExecutor",
        MockInterpreterPoolExecutor,
        raising=False,
    )

    executor = get_isolated_executor(max_workers=2)
    assert type(executor).__name__ == "MockInterpreterPoolExecutor"
