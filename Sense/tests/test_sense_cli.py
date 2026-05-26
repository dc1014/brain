from typer.testing import CliRunner
from Sense.cli import app

runner = CliRunner()


def test_scrape_command_success(monkeypatch):
    """Proves the CLI outputs clean markdown to stdout and exits with 0."""
    monkeypatch.setattr(
        "Sense.cli.transduce_web_page",
        lambda url: f'<sensory_input source="{url}">\n# Clean Output\n</sensory_input>',
    )

    result = runner.invoke(app, ["scrape", "http://safe-url.com"])

    assert result.exit_code == 0
    assert "<sensory_input" in result.stdout
    assert "# Clean Output" in result.stdout


def test_scrape_command_security_block(monkeypatch):
    """Proves the CLI returns a non-zero exit code if the receptor caught a security violation."""
    monkeypatch.setattr(
        "Sense.cli.transduce_web_page",
        lambda url: f'<sensory_error source="{url}">\nSSRF BLOCK\n</sensory_error>',
    )

    result = runner.invoke(app, ["scrape", "http://localhost"])

    assert result.exit_code == 1
    assert "SSRF BLOCK" in result.stdout


def test_scrape_command_fatal_exception(monkeypatch):
    """Proves catastrophic CLI crashes write to stderr, keeping stdout pure."""

    def mock_crash(url):
        raise RuntimeError("Complete catastrophic failure")

    monkeypatch.setattr("Sense.cli.transduce_web_page", mock_crash)

    result = runner.invoke(app, ["scrape", "http://crash-url.com"])

    assert result.exit_code == 1
    assert result.stdout == ""  # Stdout remains completely pristine


def test_cli_flush(mocker):
    mock_flush = mocker.patch("System.neuroanatomy.systemic.lymphatic.flush_waste")
    result = runner.invoke(app, ["flush"])
    assert result.exit_code == 0
    mock_flush.assert_called_once()


def test_cli_taste(mocker):
    mock_sample = mocker.patch(
        "Sense.receptors.taste.sample_file", return_value={"status": "tasty"}
    )
    result = runner.invoke(app, ["taste", "dummy.txt"])
    assert result.exit_code == 0
    assert "tasty" in result.stdout
    mock_sample.assert_called_once_with("dummy.txt")


def test_cli_listen(mocker):
    # Patch at the source module
    mock_record = mocker.patch(
        "Sense.receptors.audio.record_audio", return_value="Audio recorded"
    )
    result = runner.invoke(app, ["listen", "--duration", "1", "-o", "test.wav"])
    assert result.exit_code == 0
    assert "Hardware Mic Active" in result.stdout
    mock_record.assert_called_once()


def test_cli_speak(mocker, tmp_path):
    # Patch at the source module
    mock_play = mocker.patch("Sense.receptors.audio.play_audio")
    dummy_wav = tmp_path / "test.wav"
    dummy_wav.touch()

    result = runner.invoke(app, ["speak", str(dummy_wav)])
    assert result.exit_code == 0
    assert "Physical Speaker Active" in result.stdout
    mock_play.assert_called_once()


def test_cli_smell_clean(mocker):
    # Patch at the source module
    mocker.patch(
        "System.neuroanatomy.sensory.olfactory.process_scent_profile",
        return_value="status='clean'",
    )
    result = runner.invoke(app, ["smell", "Studio"])
    assert result.exit_code == 0
    assert "Vault smells clean" in result.stdout


def test_cli_smell_anomalies(mocker):
    # Patch at the source module
    mocker.patch(
        "System.neuroanatomy.sensory.olfactory.process_scent_profile",
        return_value="status='dirty'",
    )
    result = runner.invoke(app, ["smell", "Studio"])
    assert result.exit_code == 0
    assert "Anomalies Detected" in result.stdout


def test_cli_screenshot(mocker):
    # Patch at the source module
    mock_shot = mocker.patch(
        "Sense.receptors.vision.take_screenshot", return_value="Screenshot saved"
    )
    result = runner.invoke(app, ["screenshot", "http://local.com"])
    assert result.exit_code == 0
    assert "Screenshot saved" in result.stdout
    mock_shot.assert_called_once()
