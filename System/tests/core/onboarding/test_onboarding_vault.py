# --- System/tests/core/test_onboarding_vault.py ---
import json
from pathlib import Path
from System.core.onboarding.vault import (
    sniff_vault_paths,
    setup_obsidian_shell_commands,
)


def test_sniff_vault_paths_finds_valid_config(mocker, tmp_path: Path):
    """Proves the sniffer correctly extracts ALL vault paths from the OS JSON payload."""
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    mocker.patch("System.core.onboarding.vault.Path.home", return_value=mock_home)

    linux_path = mock_home / ".config" / "obsidian"
    linux_path.mkdir(parents=True)
    obsidian_json = linux_path / "obsidian.json"

    obsidian_json.write_text(
        json.dumps({"vaults": {"random123": {"path": "/fake/path/to/Brain-Vault"}}})
    )

    result = sniff_vault_paths()
    # ⚡ FIX: Assert against the new dictionary structure
    assert result == {"random123": "/fake/path/to/Brain-Vault"}


def test_sniff_vault_paths_returns_none_if_missing(mocker, tmp_path: Path):
    """Verifies it gracefully returns an empty dictionary if no config exists."""
    mocker.patch("System.core.onboarding.vault.Path.home", return_value=tmp_path)
    # ⚡ FIX: Assert it returns an empty dict, not None
    assert sniff_vault_paths() == {}


def test_setup_obsidian_shell_commands(tmp_path: Path):
    """Proves Brain hotkeys are atomically injected into the vault configuration."""
    vault = tmp_path / "MyVault"
    vault.mkdir()

    success = setup_obsidian_shell_commands(vault)
    assert success

    hotkeys_file = vault / ".obsidian" / "hotkeys.json"
    assert hotkeys_file.exists()

    # Verify the JSON was mutated correctly
    data = json.loads(hotkeys_file.read_text())
    assert "obsidian-shellcommands:shell-command-1" in data
    assert data["obsidian-shellcommands:shell-command-1"][0]["key"] == "S"
    assert "Mod" in data["obsidian-shellcommands:shell-command-1"][0]["modifiers"]
