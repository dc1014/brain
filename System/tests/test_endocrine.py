import os
import pytest
from System.endocrine import (
    release_cortisol,
    release_dopamine,
    is_cortisol_active,
    is_dopamine_active,
)


@pytest.fixture(autouse=True)
def clean_env():
    """Ensure the bloodstream is clean before and after each test."""
    os.environ.pop("BRAIN_OS_CORTISOL", None)
    os.environ.pop("BRAIN_OS_HEADLESS", None)
    os.environ.pop("BRAIN_OS_DOPAMINE", None)
    yield
    os.environ.pop("BRAIN_OS_CORTISOL", None)
    os.environ.pop("BRAIN_OS_HEADLESS", None)
    os.environ.pop("BRAIN_OS_DOPAMINE", None)


def test_cortisol_release():
    """Proves Cortisol overrides the environment and activates headless execution."""
    assert not is_cortisol_active()
    release_cortisol()
    assert is_cortisol_active()
    assert os.environ.get("BRAIN_OS_HEADLESS") == "1", (
        "Cortisol failed to bypass security gates!"
    )


def test_dopamine_release():
    """Proves Dopamine activates exploration state."""
    assert not is_dopamine_active()
    release_dopamine()
    assert is_dopamine_active()
