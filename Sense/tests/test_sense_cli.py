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
