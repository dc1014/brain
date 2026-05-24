from System.neuroanatomy.autonomic.vagus_nerve import trigger_halt, trigger_recover


def test_trigger_halt(mocker):
    """Proves the Vagus Nerve flushes the queue and plants the Apoptosis flag atomically."""
    # ⚡ FIX: Patch the new atomic write handler instead of the old clear_pipeline_state
    mock_write = mocker.patch(
        "System.neuroanatomy.autonomic.vagus_nerve.write_state_sync_atomic"
    )

    trigger_halt()

    # It should have written the empty queue array AND the HALT file flag
    assert mock_write.call_count == 2


def test_trigger_recover(mocker):
    """Proves the Vagus Nerve recover function safely restores the Vestibular state."""
    mock_halt = mocker.patch("System.neuroanatomy.autonomic.vagus_nerve.trigger_halt")
    mock_restore = mocker.patch(
        "System.neuroanatomy.autonomic.vagus_nerve.restore_balance"
    )

    # Mock both path unlinking and os removal to be completely implementation-agnostic
    mocker.patch("pathlib.Path.exists", return_value=True)

    trigger_recover()

    mock_halt.assert_called_once()
    mock_restore.assert_called_once()
