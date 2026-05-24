from System.neuroanatomy.systemic.thymus import ThymusGland


def test_thymus_dynamic_address():
    """Zero-Debt: Proves IPC addresses dynamically rotate to prevent multithread collision."""
    t1 = ThymusGland()
    t2 = ThymusGland()
    assert t1.address != t2.address


def test_thymus_analyze_event_velocity(mocker):
    """Zero-Debt: Proves the Thymus triggers an escalation if destructive mutation limits are breached."""
    thymus = ThymusGland()
    mock_escalate = mocker.patch.object(thymus, "_escalate")

    # Prove non-destructive actions are ignored
    thymus._analyze_event({"impact": "read_only"})
    assert len(thymus.destructive_velocity_window) == 0

    # Flood the system safely up to the absolute limit
    for _ in range(thymus.MAX_MUTATIONS):
        thymus._analyze_event({"impact": "destructive"})

    assert mock_escalate.call_count == 0

    # ⚡ The breaking point: One more action triggers the alarm
    thymus._analyze_event({"impact": "destructive"})
    mock_escalate.assert_called_once()


def test_thymus_escalation(mocker):
    """Zero-Debt: Proves the escalation chain cascades correctly (Halt -> Kill -> Rollback)."""
    thymus = ThymusGland()

    # Target the TRUE origin paths for locally-imported functions!
    mock_halt = mocker.patch("System.neuroanatomy.autonomic.vagus_nerve.trigger_halt")
    mock_restore = mocker.patch(
        "System.neuroanatomy.autonomic.vestibular.restore_balance"
    )

    # time.sleep is imported globally in thymus.py, so mocking it on the module works
    mocker.patch("System.neuroanatomy.systemic.thymus.time.sleep")

    mock_proc = mocker.MagicMock()
    mock_proc.poll.return_value = (
        None  # Trick the Thymus into thinking Medulla is stuck
    )
    thymus.medulla_process = mock_proc

    thymus._escalate()

    mock_halt.assert_called_once()
    mock_proc.kill.assert_called_once()
    mock_restore.assert_called_once()


def test_medulla_child_boot(mocker):
    """Zero-Debt: Proves the Medulla child-boot sequence links the IPC socket properly."""
    from System.neuroanatomy.autonomic.medulla import child_boot

    # Target the true multiprocessing library origin for the Client mock
    mock_client = mocker.patch("multiprocessing.connection.Client")
    mock_medulla = mocker.patch(
        "System.neuroanatomy.autonomic.medulla.MedullaOblongata"
    )
    instance = mock_medulla.return_value

    # Force the infinite while-loop to instantly exit
    mocker.patch(
        "System.neuroanatomy.autonomic.medulla.time.sleep",
        side_effect=KeyboardInterrupt,
    )

    child_boot("fake_test_address")

    instance.wake.assert_called_once()
    instance.stop.assert_called_once()
    assert instance.ipc_client == mock_client.return_value
