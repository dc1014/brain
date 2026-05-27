from typer.testing import CliRunner

from System.cli import app


def test_print_daydream_outputs_tail(tmp_path):
    ledger = tmp_path / "daydreams.md"
    ledger.write_text("one\ntwo\nthree\n", encoding="utf-8")

    result = CliRunner().invoke(
        app, ["print-daydream", "--path", str(ledger), "--lines", "2"]
    )

    assert result.exit_code == 0
    assert "two" in result.stdout
    assert "three" in result.stdout
    assert "one" not in result.stdout


def test_setup_prompts_to_install_missing_python():
    text = open("setup.sh", encoding="utf-8").read()

    assert "install_python_runtime" in text
    assert "Install Python prerequisites now?" in text
    assert "python3-venv" in text
