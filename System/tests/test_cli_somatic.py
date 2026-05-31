import pytest
from pathlib import Path
from unittest.mock import patch


def test_watch_daemon_normalizes_typer_option_regression(
    mocker, tmp_path: Path
) -> None:
    """Proves the somatosensory watch daemon handles non-integer OptionInfo objects
    gracefully when invoked programmatically by background daemon threads.
    """
    from System.cli_somatic import watch

    mocker.patch("System.cli_somatic.ROOT_DIR", tmp_path)
    mocker.patch("System.cli_somatic.MirrorNeurons")
    mocker.patch(
        "System.cli_somatic.time.sleep",
        side_effect=KeyboardInterrupt("Refractory Guard Passed"),
    )

    mock_option_info = mocker.MagicMock()

    with pytest.raises(KeyboardInterrupt, match="Refractory Guard Passed"):
        watch(max_loops=mock_option_info)


def test_reflex_blocks_dangerous_ast_calls(mocker, tmp_path: Path) -> None:
    """Proves the Spinal AST scanner blocks os.system before loading into WASM."""
    from System.cli_somatic import reflex

    mocker.patch("System.cli_somatic.ROOT_DIR", tmp_path)
    engram_dir = tmp_path / "System" / "tools" / "engrams"
    engram_dir.mkdir(parents=True, exist_ok=True)

    engram_file = engram_dir / "bad_reflex.py"
    engram_file.write_text("import os\nos.system('rm -rf /')\n", encoding="utf-8")

    with patch("System.cli_somatic.console.print") as mock_print:
        reflex("bad_reflex")

    mock_print.assert_any_call(
        "[bold red]Spinal Security Block: Engram contains dangerous call 'system'. Execution denied.[/bold red]"
    )


def test_reflex_routes_to_sandbox_safely(mocker, tmp_path: Path) -> None:
    """Proves safe engrams are safely routed to the Pyodide execute_in_sandbox function."""
    from System.cli_somatic import reflex
    from System.core.schemas import ExecutionResult

    mocker.patch("System.cli_somatic.ROOT_DIR", tmp_path)
    engram_dir = tmp_path / "System" / "tools" / "engrams"
    engram_dir.mkdir(parents=True, exist_ok=True)

    engram_file = engram_dir / "safe_reflex.py"
    engram_file.write_text(
        "def execute_reflex():\n    print('Hello Sandbox')\n", encoding="utf-8"
    )

    # Create an async mock for execute_in_sandbox
    async def mock_run(*args, **kwargs):
        return ExecutionResult(success=True, output="Hello Sandbox", block_reason=None)

    # ⚡ FIX: Patch the module where the function actually lives,
    # since cli_somatic imports it locally inside the reflex() scope.
    mock_execute = mocker.patch(
        "System.tools.sandbox.execute_in_sandbox", side_effect=mock_run
    )

    with patch("System.cli_somatic.console.print") as mock_print:
        reflex("safe_reflex")

    # Verify the sandbox was called correctly
    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert kwargs["route"] == "CODE_GENERATION"
    assert "execute_reflex()" in kwargs["command"][2]

    mock_print.assert_any_call(
        "[bold green]Reflex completed safely inside the sandbox.[/bold green]"
    )


def test_expose_dermis_captures_cloudflare_url(mocker, tmp_path: Path) -> None:
    """Proves the Dermis tunnel manager correctly parses and saves the public URL."""
    from System.cli_somatic import expose_dermis
    import time

    mocker.patch("System.cli_somatic.ROOT_DIR", tmp_path)

    # Mock shutil.which to pretend cloudflared is installed
    mocker.patch(
        "System.cli_somatic.shutil.which", return_value="/usr/local/bin/cloudflared"
    )

    # We need to spy on Path.write_text to prove the URL was saved before cleanup
    mock_write = mocker.patch("System.cli_somatic.Path.write_text")

    # Create a mock Popen object that simulates Cloudflare's terminal output
    mock_process = mocker.MagicMock()
    mock_process.stdout.readline.side_effect = [
        "INF Starting tunnel...\n",
        "INF  https://purple-monkey-dishwasher.trycloudflare.com \n",
        "",  # EOF
    ]

    def wait_side_effect():
        time.sleep(0.1)
        raise KeyboardInterrupt()

    mock_process.wait.side_effect = wait_side_effect
    mocker.patch("System.cli_somatic.subprocess.Popen", return_value=mock_process)

    result = expose_dermis(8080)

    assert result == "Tunnel manually closed by user."

    # Allow the daemon thread to finish processing the lines
    time.sleep(0.2)

    # Prove the URL was correctly extracted and saved
    mock_write.assert_called_once_with(
        "https://purple-monkey-dishwasher.trycloudflare.com", encoding="utf-8"
    )
