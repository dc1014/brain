import yaml  # type: ignore
import hashlib
from typing import Any
from rich.console import Console

from System.core.paths import ROOT_DIR

console = Console()

_cached_config: dict[str, Any] = {}
_cached_hash: str = ""


def _compute_dna_hash() -> str:
    """Computes an MD5 hash of all DNA YAML files to detect neuroplastic mutations."""
    config_dir = ROOT_DIR / "System" / "config"
    config_files = [
        "models.yaml",
        "agents.yaml",
        "routes.yaml",
        "medulla.yaml",
        "webhooks.yaml",
        "tools.yaml",
    ]
    hasher = hashlib.md5()
    for file in config_files:
        filepath = config_dir / file
        if filepath.exists():
            with open(filepath, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()


def get_dna_config(force_reload: bool = False) -> dict[str, Any]:
    """Lazy-loads and caches the OS genetic code, hot-reloading if files mutate."""
    global _cached_config, _cached_hash

    current_hash = _compute_dna_hash()

    # 1. Return cached memory if the DNA hasn't mutated
    if _cached_config and current_hash == _cached_hash and not force_reload:
        return _cached_config

    # 2. Log the hot-reload if the system was already booted
    if _cached_config:
        console.print(
            "[dim cyan]🧬 Neuroplasticity: DNA mutation detected. Hot-reloading config...[/dim cyan]"
        )

    config_dir = ROOT_DIR / "System" / "config"

    try:
        from System.neuroanatomy.pathways.polymerase import proofread_yaml_dna
        from System.core.config_proofreader import proofread_global_config

        # 🧬 DNA POLYMERASE: Proofread the OS genetic code
        proofread_yaml_dna(config_dir)

        config_files = [
            "models.yaml",
            "agents.yaml",
            "routes.yaml",
            "medulla.yaml",
            "webhooks.yaml",
            "tools.yaml",
        ]

        raw_config: dict[str, Any] = {}
        for file in config_files:
            filepath = config_dir / file
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    raw_config.update(yaml.safe_load(f) or {})

        # 🛡️ IMMUNE SYSTEM: Validate structural integrity
        validated_dna = proofread_global_config(raw_config)

        # 3. Update the global cache state
        _cached_config = validated_dna.model_dump()
        _cached_hash = current_hash
        return _cached_config

    except Exception as e:
        console.print(
            f"[bold red]BOOT WARNING: Config DNA failed to load ({e}).[/bold red]"
        )
        return {"agents": {}, "routes": {}, "models": {}}
