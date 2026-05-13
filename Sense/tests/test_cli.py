from typer.testing import CliRunner
from cli import app

runner = CliRunner()


def test_scrape_command_success(monkeypatch):
    """Proves the CLI outputs clean markdown to stdout and exits with 0."""
    # Mock the underlying receptor to bypass network calls
    monkeypatch.setattr(
        "cli.transduce_web_page",
        lambda url: f'<sensory_input source="{url}">\n# Clean Output\n</sensory_input>',
    )

    result = runner.invoke(app, ["http://safe-url.com"])

    assert result.exit_code == 0
    assert "<sensory_input" in result.stdout
    assert "# Clean Output" in result.stdout


def test_scrape_command_security_block(monkeypatch):
    """Proves the CLI returns a non-zero exit code if the receptor caught a security violation."""
    # Mock the receptor returning a security error
    monkeypatch.setattr(
        "cli.transduce_web_page",
        lambda url: f'<sensory_error source="{url}">\nSSRF BLOCK\n</sensory_error>',
    )

    result = runner.invoke(app, ["http://localhost"])

    # It must exit with 1 so bash scripts/Forge know the scrape failed
    assert result.exit_code == 1
    # The error payload should still be printed so the LLM can read *why* it failed
    assert "SSRF BLOCK" in result.stdout


def test_scrape_command_fatal_exception(monkeypatch):
    """Proves catastrophic CLI crashes write to stderr, keeping stdout pure."""

    def mock_crash(url):
        raise RuntimeError("Complete catastrophic failure")

    monkeypatch.setattr("cli.transduce_web_page", mock_crash)

    result = runner.invoke(app, ["http://crash-url.com"])

    assert result.exit_code == 1
    assert result.stdout == ""  # Stdout remains completely pristine
    # We can't directly assert result.stderr with Typer's default test runner easily,
    # but asserting stdout is empty proves the separation.
