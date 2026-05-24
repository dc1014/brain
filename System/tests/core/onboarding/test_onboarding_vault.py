import json
from pathlib import Path
from System.core.onboarding.vault import (
    sniff_vault_paths,
    setup_obsidian_shell_commands,
)


def test_sniff_vault_paths_nonexistent(tmp_path: Path, monkeypatch):
    """Proves sniffing returns an empty dict if no Obsidian configuration is discovered."""
    # Point the home resolution to our isolated temporary path
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    vaults = sniff_vault_paths()
    assert vaults == {}


def test_sniff_vault_paths_discovery(tmp_path: Path, monkeypatch):
    """Proves that active config files are successfully scanned and unpacked."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # Simulate a standard roaming configuration folder footprint
    roaming_dir = tmp_path / "AppData" / "Roaming" / "obsidian"
    roaming_dir.mkdir(parents=True)

    mock_config = {
        "vaults": {
            "v1": {"path": "/Users/Admin/VaultAlpha"},
            "v2": {"path": "/Users/Admin/VaultBeta"},
        }
    }

    config_file = roaming_dir / "obsidian.json"
    config_file.write_text(json.dumps(mock_config), encoding="utf-8")

    vaults = sniff_vault_paths()
    assert "v1" in vaults
    assert vaults["v2"] == "/Users/Admin/VaultBeta"


def test_setup_obsidian_shell_commands_agnostic_skip(tmp_path: Path):
    """Proves that a non-Obsidian text workspace is safely bypassed without pollution."""
    standard_folder = tmp_path / "GenericWorkspace"
    standard_folder.mkdir()

    # Should return False and make no edits since `.obsidian` is completely missing
    success = setup_obsidian_shell_commands(standard_folder)
    assert not success
    assert not (standard_folder / ".obsidian").exists()


def test_setup_obsidian_shell_commands_active_injection(tmp_path: Path):
    """Proves hotkeys are atomically injected when a valid Obsidian vault is detected."""
    vault = tmp_path / "MyObsidianVault"
    obsidian_dir = vault / ".obsidian"
    obsidian_dir.mkdir(parents=True)

    # Trigger active context onboarding injection setup
    success = setup_obsidian_shell_commands(vault)
    assert success

    hotkeys_path = obsidian_dir / "hotkeys.json"
    assert hotkeys_path.exists()

    with open(hotkeys_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "obsidian-shellcommands:shell-command-1" in data
