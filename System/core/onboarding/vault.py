# --- System/core/onboarding/vault.py ---
import json
from pathlib import Path
from typing import Dict, Any
from System.core.onboarding.security import _atomic_write_text


def sniff_vault_paths() -> Dict[str, str]:
    """Cross-platform heuristics to find ALL Obsidian Vaults."""
    home = Path.home()
    paths = [
        home / "Library" / "Application Support" / "obsidian" / "obsidian.json",
        home / "AppData" / "Roaming" / "obsidian" / "obsidian.json",
        home / ".config" / "obsidian" / "obsidian.json",
        home
        / ".var"
        / "app"
        / "md.obsidian.Obsidian"
        / "config"
        / "obsidian"
        / "obsidian.json",
    ]

    found_vaults = {}
    for p in paths:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                vaults = data.get("vaults", {})
                for v_id, v_data in vaults.items():
                    found_vaults[v_id] = v_data.get("path")
                if found_vaults:
                    return found_vaults
            except Exception:
                continue
    return found_vaults


def setup_obsidian_shell_commands(vault_path: Path) -> bool:
    """
    Injects Brain terminal execution commands and hotkeys (Ctrl+Alt+S)
    safely into the Obsidian vault's plugin configuration matrix.

    UNIX PHILOSOPHY FIX: If the directory is not a pre-existing Obsidian vault,
    this gracefully aborts to avoid polluting standard text workspaces.
    """
    try:
        obsidian_dir = vault_path / ".obsidian"

        # ⚡ Do not force-create an Obsidian context in a generic workspace
        if not obsidian_dir.exists():
            return False

        # 1. Safely Configure Hotkeys
        hotkeys_path = obsidian_dir / "hotkeys.json"
        hotkeys_data = {}
        if hotkeys_path.exists():
            try:
                hotkeys_data = json.loads(hotkeys_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Inject our Ctrl+Alt+S hotkey
        hotkeys_data["obsidian-shellcommands:shell-command-1"] = [
            {"modifiers": ["Mod", "Alt"], "key": "S"}
        ]

        _atomic_write_text(hotkeys_path, json.dumps(hotkeys_data, indent=2))

        # 2. Configure Shell Commands Plugin Data
        plugins_dir = obsidian_dir / "plugins" / "obsidian-shellcommands"
        plugins_dir.mkdir(parents=True, exist_ok=True)

        sc_data_path = plugins_dir / "data.json"
        sc_data: Dict[str, Any] = {"shell_commands": []}
        if sc_data_path.exists():
            try:
                sc_data = json.loads(sc_data_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        _atomic_write_text(sc_data_path, json.dumps(sc_data, indent=2))

        return True
    except Exception:
        return False
