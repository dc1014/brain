# --- System/tests/autonomic/test_vagus_nerve.py ---
import pytest
import System.neuroanatomy.autonomic.vagus_nerve as vagus_mod
from System.neuroanatomy.autonomic.vagus_nerve import trigger_halt, trigger_recover


@pytest.fixture(autouse=True)
def isolate_vagus_signal(tmp_path, monkeypatch):
    """Isolates the halt signal file to a temporary directory for safe testing."""
    monkeypatch.setattr(vagus_mod, "SIGNAL_FILE", tmp_path / ".vagus_abort_signal")


def test_trigger_halt(tmp_path):
    """Proves the vagus nerve can safely drop an atomic halt flag."""
    trigger_halt()
    signal_file = tmp_path / ".vagus_abort_signal"

    assert signal_file.exists()
    assert signal_file.read_text(encoding="utf-8") == "HALT_SIGNAL"


def test_trigger_recover(tmp_path):
    """Proves the vagus nerve clears the atomic halt flag."""
    signal_file = tmp_path / ".vagus_abort_signal"
    signal_file.write_text("HALT_SIGNAL", encoding="utf-8")

    trigger_recover()

    assert not signal_file.exists()
