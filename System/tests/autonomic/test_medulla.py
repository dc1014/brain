from System.neuroanatomy.autonomic.medulla import MedullaOblongata


def test_medulla_blueprint_parsing(tmp_path, monkeypatch):
    """Proves the Medulla correctly digests configuration params from medulla.yaml structures."""
    config_file = tmp_path / "medulla.yaml"
    mock_yaml = (
        "medulla:\n"
        "  state_parameters:\n"
        "    awake_port: 9000\n"
        "  background_daemons:\n"
        "    file_watcher:\n"
        "      enabled: false\n"
    )
    config_file.write_text(mock_yaml, encoding="utf-8")

    medulla = MedullaOblongata()
    monkeypatch.setattr(medulla, "config_path", config_file)
    refreshed_config = medulla._load_blueprint()

    assert refreshed_config["state_parameters"]["awake_port"] == 9000
    assert refreshed_config["background_daemons"]["file_watcher"]["enabled"] is False


def test_medulla_lifecycle_execution(mocker):
    """Proves the Medulla can awaken active loops cleanly and shut them down without hanging."""
    mocker.patch("System.neuroanatomy.autonomic.medulla.threading.Thread")

    brainstem = MedullaOblongata()
    assert brainstem.is_alive is False

    brainstem.wake()
    assert brainstem.is_alive is True

    brainstem.stop()
    assert brainstem.is_alive is False


def test_medulla_cognitive_heartbeat_execution(mocker):
    """Manually invokes the heartbeat loop to secure line coverage safely."""
    mock_queue_runner = mocker.patch("System.core.orchestrator.run_pending_queue")
    mocker.patch("System.neuroanatomy.autonomic.medulla.time.sleep")

    brainstem = MedullaOblongata()
    brainstem.is_alive = True

    def break_loop():
        brainstem.is_alive = False

    mock_queue_runner.side_effect = break_loop

    brainstem._cognitive_heartbeat()
    mock_queue_runner.assert_called_once()


def test_medulla_respiratory_thread_supervision(mocker):
    """Fires the supervisory branch to track thread monitoring and resuscitation paths."""
    brainstem = MedullaOblongata()
    brainstem.is_alive = True
    brainstem.config_data = {
        "background_daemons": {
            "dermis_receptor": {"enabled": True, "secure_port": 8080},
            "file_watcher": {"enabled": True},
        }
    }

    # Patch the abstraction directly at its module origin namespace
    mock_dermis = mocker.patch("Sense.receptors.dermis.DermisAbstraction")

    # Configure the mock to return a safe instance proxy structure
    mock_instance = mocker.MagicMock()
    mock_dermis.return_value = mock_instance

    # Stub out somatic file watcher dependencies to isolate the thread tracking logic
    mocker.patch("System.cli_somatic.watch")

    # Configure a mock thread object that reports its runtime health as alive
    mock_live_thread = mocker.MagicMock()
    mock_live_thread.is_alive.return_value = (
        True  # Tells the second loop frame the daemon is alive!
    )

    # ⚡ THE LINTER FIX: Remove the unused variable 'mock_thread_class =' assignment
    mocker.patch(
        "System.neuroanatomy.autonomic.medulla.threading.Thread",
        return_value=mock_live_thread,
    )

    # Simulate an empty daemons tracking ledger (forcing initial resuscitation)
    brainstem.daemons = {}

    # Break the infinite loop block on the second evaluation frame cycle safely
    mocker.patch(
        "System.neuroanatomy.autonomic.medulla.time.sleep",
        side_effect=[None, Exception("Loop Break")],
    )

    try:
        brainstem._supervise_threads()
    except Exception as e:
        if str(e) != "Loop Break":
            raise e

    # Assert that the abstraction was invoked and assigned to the structural tracking state on the first loop
    mock_dermis.assert_called_once_with(port=8080)
    assert "dermis" in brainstem.daemons
