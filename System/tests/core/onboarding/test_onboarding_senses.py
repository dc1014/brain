# --- System/tests/core/test_onboarding_senses.py ---
import subprocess
from System.core.onboarding.senses import (
    install_optional_feature,
    install_playwright_chromium,
)


def test_install_optional_feature_success(mocker):
    """Proves the uv pip install targets the correct package and returns True on success."""
    mock_run = mocker.patch("System.core.onboarding.senses.subprocess.run")
    mock_run.return_value.returncode = 0

    assert install_optional_feature("vision")

    # Verify it called the correct command
    called_args = mock_run.call_args[0][0]
    assert called_args == ["uv", "pip", "install", ".[vision]"]


def test_install_optional_feature_failure(mocker):
    """Proves it returns False if the pip install crashes."""
    mock_run = mocker.patch("System.core.onboarding.senses.subprocess.run")
    mock_run.return_value.returncode = 1

    assert not install_optional_feature("audio")


def test_install_playwright_chromium_timeout_fallback(mocker):
    """DEFCON PROOF: Verifies the installation fails closed if the Chromium download hangs."""
    # Force the mock to raise a TimeoutExpired exception
    mocker.patch(
        "System.core.onboarding.senses.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="playwright", timeout=1),
    )

    # The function should catch the exception and gracefully return False
    assert not install_playwright_chromium(timeout_seconds=1)
