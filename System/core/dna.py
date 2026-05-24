import yaml  # type: ignore
import hashlib
from typing import Any
from rich.console import Console

from System.core.paths import ROOT_DIR

console = Console()

_cached_config: dict[str, Any] = {}
_cached_hash: str = ""

CONFIG_FILES = ["system.yaml", "agents.yaml", "tools.yaml"]


def _compute_dna_hash() -> str:
    """Computes a composite MD5 hash across the config triad to detect mutations."""
    config_dir = ROOT_DIR / "System" / "config"
    hasher = hashlib.md5()
    for file in CONFIG_FILES:
        filepath = config_dir / file
        if filepath.exists():
            with open(filepath, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()


def get_dna_config(force_reload: bool = False) -> dict[str, Any]:
    """Lazy-loads and caches configuration matrix layers, hot-reloading on file modification."""
    global _cached_config, _cached_hash

    current_hash = _compute_dna_hash()

    if _cached_config and current_hash == _cached_hash and not force_reload:
        return _cached_config

    if _cached_config:
        console.print(
            "[dim cyan]⚙️ Configuration change detected. Hot-reloading config triad...[/dim cyan]"
        )

    config_dir = ROOT_DIR / "System" / "config"

    try:
        from System.core.config_proofreader import proofread_global_config

        raw_config: dict[str, Any] = {}
        for file in CONFIG_FILES:
            filepath = config_dir / file
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    raw_config.update(yaml.safe_load(f) or {})

        # Validate unified structural schema compliance via Pydantic
        validated_dna = proofread_global_config(raw_config)

        _cached_config = validated_dna.model_dump()
        _cached_hash = current_hash
        return _cached_config

    except Exception as e:
        console.print(
            f"[bold red]BOOT WARNING: Failed to load config triad ({e}).[/bold red]"
        )
        return {"agents": {}, "routes": {}, "models": {}, "tools": {}}
