import os
from System.neuroanatomy.autonomic.vagus_nerve import trigger_halt, trigger_recover
from System.core.paths import ROOT_DIR, normalize_path


def test_trigger_halt(mocker):
    """Proves the Vagus Nerve flushes the queue and plants the Apoptosis flag."""
    mock_clear = mocker.patch(
        "System.neuroanatomy.autonomic.vagus_nerve.clear_pipeline_state"
    )

    trigger_halt()

    mock_clear.assert_called_once()
    abort_flag = normalize_path(ROOT_DIR / "System" / ".vagus_abort_signal")
    assert abort_flag.exists()

    # Cleanup
    try:
        os.remove(abort_flag)
    except OSError:
        pass


def test_trigger_recover(mocker):
    """Proves the Vagus Nerve halts operations, triggers rollback, and cleans the signal."""
    mock_halt = mocker.patch("System.neuroanatomy.autonomic.vagus_nerve.trigger_halt")
    mock_restore = mocker.patch(
        "System.neuroanatomy.autonomic.vagus_nerve.restore_balance"
    )

    # Plant a fake flag to ensure it gets cleaned up
    abort_flag = normalize_path(ROOT_DIR / "System" / ".vagus_abort_signal")
    abort_flag.write_text("HALT", encoding="utf-8")

    trigger_recover()

    mock_halt.assert_called_once()
    mock_restore.assert_called_once()

    # Prove the signal was successfully cleared so the OS can boot next time
    assert not abort_flag.exists()
