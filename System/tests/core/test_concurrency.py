import sys
from unittest.mock import patch
from System.core.concurrency import lock_concurrency_defaults


@patch("multiprocessing.set_start_method")
def test_lock_concurrency_defaults_unix(mock_set_start_method, monkeypatch):
    """🛡️ ZERO-DEBT PROOF: Verifies forkserver is rigidly enforced on Unix systems."""
    monkeypatch.setattr(sys, "platform", "linux")
    lock_concurrency_defaults()
    mock_set_start_method.assert_called_once_with("forkserver")


@patch("multiprocessing.set_start_method")
def test_lock_concurrency_defaults_windows(mock_set_start_method, monkeypatch):
    """🛡️ ZERO-DEBT PROOF: Verifies Windows gracefully ignores the Unix process lock."""
    monkeypatch.setattr(sys, "platform", "win32")
    lock_concurrency_defaults()
    mock_set_start_method.assert_not_called()


@patch(
    "multiprocessing.set_start_method",
    side_effect=RuntimeError("context has already been set"),
)
def test_lock_concurrency_defaults_idempotent(mock_set_start_method, monkeypatch):
    """🛡️ ZERO-DEBT PROOF: Verifies the lock doesn't crash if called multiple times (e.g., during pytest loops)."""
    monkeypatch.setattr(sys, "platform", "darwin")
    # Should safely catch the RuntimeError and pass
    lock_concurrency_defaults()
    mock_set_start_method.assert_called_once()
