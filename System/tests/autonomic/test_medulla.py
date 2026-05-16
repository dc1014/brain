from System.neuroanatomy.autonomic.medulla import MedullaOblongata


def test_medulla_blueprint_parsing(tmp_path, monkeypatch):
    """Proves the Medulla correctly digests configuration params from medulla.yaml mapping structures."""
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
