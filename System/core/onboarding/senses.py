# --- System/core/onboarding/senses.py ---
import subprocess
from System.core.paths import ROOT_DIR


def install_optional_feature(feature_flag: str) -> bool:
    """
    Safely executes an isolated `uv pip install` for a specific feature flag.
    Returns True if the installation succeeded, False otherwise.
    """
    try:
        # We enforce `cwd=ROOT_DIR` to guarantee uv targets the correct project environment
        res = subprocess.run(
            ["uv", "pip", "install", f".[{feature_flag}]"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
        )
        return res.returncode == 0
    except Exception:
        return False


def install_playwright_chromium(timeout_seconds: int = 60) -> bool:
    """
    Attempts to download the Playwright Chromium binary.
    Wraps the process in a strict timeout to prevent indefinite hangs.
    """
    try:
        res = subprocess.run(
            ["uv", "run", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=ROOT_DIR,
        )
        return res.returncode == 0
    except subprocess.TimeoutExpired:
        # If the download takes longer than 60s, we fail closed gracefully
        return False
    except Exception:
        return False
