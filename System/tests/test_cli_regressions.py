from typer.testing import CliRunner

from System.cli import app


def test_map_topology_cli_smoke(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["map-topology"])

    assert result.exit_code == 0
    assert "ImportError" not in result.stdout
    assert "cannot import name" not in result.stdout


def test_list_reflexes_cli_smoke():
    result = CliRunner().invoke(app, ["list-reflexes"])

    assert result.exit_code == 0
    assert "Reflex Arc Triggered" in result.stdout
