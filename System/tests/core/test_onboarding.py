import json
import pytest
import urllib.error
from System.core.onboarding import (
    scan_ollama,
    sniff_obsidian_vaults,
    setup_obsidian_shell_commands,
    validate_key_live,
    check_host_binary,
    calibrate_model_dna,
)


@pytest.mark.asyncio
async def test_validate_key_live_authorized(mocker):
    mock_res = mocker.MagicMock()
    mock_res.read.return_value = b"{}"
    mocker.patch(
        "System.core.onboarding.urllib.request.urlopen",
        return_value=mocker.MagicMock(
            __enter__=mocker.MagicMock(return_value=mock_res)
        ),
    )
    ok, msg = await validate_key_live(
        "OPENAI_API_KEY", "sk-proj-validKeyFormat1234567890abcdef1234567890abcdef"
    )
    assert ok is True
    assert "live and authorized" in msg


@pytest.mark.asyncio
async def test_validate_key_live_revoked(mocker):
    fp = mocker.MagicMock()
    mock_http_error = urllib.error.HTTPError(
        url="https://api.openai.com/v1/models",
        code=401,
        msg="Unauthorized",
        hdrs=mocker.MagicMock(),
        fp=fp,
    )
    mocker.patch(
        "System.core.onboarding.urllib.request.urlopen", side_effect=mock_http_error
    )
    ok, msg = await validate_key_live(
        "OPENAI_API_KEY", "sk-proj-revokedKeyFormat1234567890abcdef1234567890abcdef"
    )
    assert ok is False
    assert "Authentication Rejected" in msg


@pytest.mark.asyncio
async def test_check_host_binary_found(mocker):
    mocker.patch("System.core.onboarding.shutil.which", return_value="/usr/bin/git")
    res = await check_host_binary("git")
    assert res is True


@pytest.mark.asyncio
async def test_scan_ollama_online(mocker):
    mock_payload = json.dumps(
        {"models": [{"name": "llama3:latest"}, {"name": "qwen2.5:7b"}]}
    ).encode("utf-8")
    mock_read = mocker.MagicMock()
    mock_read.read.return_value = mock_payload
    mocker.patch(
        "System.core.onboarding.urllib.request.urlopen",
        return_value=mocker.MagicMock(
            __enter__=mocker.MagicMock(return_value=mock_read)
        ),
    )
    live, models = await scan_ollama()
    assert live is True
    assert "llama3:latest" in models


@pytest.mark.asyncio
async def test_sniff_obsidian_vaults_resolution(tmp_path, monkeypatch):
    config_dir = tmp_path / "obsidian"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "obsidian.json"
    vault_dir = tmp_path / "MyNotesVault"
    vault_dir.mkdir()
    payload = {"vaults": {"v1": {"path": str(vault_dir)}}}
    config_file.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(
        "System.core.onboarding.sys", type("sys", (), {"platform": "win32"})()
    )
    vaults = await sniff_obsidian_vaults()
    assert len(vaults) == 1
    assert vaults[0] == vault_dir


def test_calibrate_model_dna_gemini_only(tmp_path, monkeypatch):
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)
    yaml_file = config_dir / "models.yaml"
    initial_yaml = "models:\n  fast: 'openai/gpt-4o-mini'\n  premium: 'openai/gpt-4o'\n  default: 'openai/gpt-4o-mini'"
    yaml_file.write_text(initial_yaml, encoding="utf-8")
    monkeypatch.setattr("System.core.onboarding.ROOT_DIR", tmp_path)
    success = calibrate_model_dna(["GEMINI_API_KEY"])
    assert success is True
    updated_text = yaml_file.read_text(encoding="utf-8")
    assert "gemini/gemini-2.5-flash" in updated_text


def test_setup_obsidian_shell_commands_payload_and_activation(tmp_path):
    vault_path = tmp_path / "TargetVault"
    vault_path.mkdir()
    obsidian_dir = vault_path / ".obsidian"
    obsidian_dir.mkdir()
    ok = setup_obsidian_shell_commands(vault_path)
    assert ok is True
    app_data = json.loads((obsidian_dir / "app.json").read_text(encoding="utf-8"))
    assert app_data["legacyCommunityPlugins"] is False


def test_setup_obsidian_shell_commands_non_destructive_merge(tmp_path):
    """Zero-Debt Test: Proves that configuring commands does NOT overwrite a user's pre-existing shell commands."""
    vault_path = tmp_path / "UserActiveVault"
    vault_path.mkdir()
    obsidian_dir = vault_path / ".obsidian"
    plugins_dir = obsidian_dir / "plugins" / "obsidian-shellcommands"
    plugins_dir.mkdir(parents=True)

    user_payload = {
        "settings": {
            "commands": [
                {
                    "id": "user-custom-backup",
                    "name": "My Custom Sync Script",
                    "command": "rclone sync ./ paths",
                }
            ]
        }
    }
    (plugins_dir / "data.json").write_text(json.dumps(user_payload), encoding="utf-8")

    success = setup_obsidian_shell_commands(vault_path)
    assert success is True

    merged_data = json.loads((plugins_dir / "data.json").read_text(encoding="utf-8"))
    merged_cmds = merged_data["settings"]["commands"]
    assert any(c["id"] == "user-custom-backup" for c in merged_cmds), (
        "Catastrophic Bug: User's pre-existing commands wiped out!"
    )
