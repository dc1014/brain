import yaml  # type: ignore
from typing import Any
from rich.console import Console

from System.core.paths import ROOT_DIR

console = Console()


def _load_dna() -> dict[str, Any]:
    """Loads and proofreads the OS genetic code into a global state."""
    config_dir = ROOT_DIR / "System" / "config"

    try:
        from System.neuroanatomy.pathways.polymerase import proofread_yaml_dna
        from System.core.config_proofreader import proofread_global_config

        # 🧬 DNA POLYMERASE: Proofread the OS genetic code before booting
        proofread_yaml_dna(config_dir)

        # ⚡ SHIFT-LEFT: Unifying the Limbic Config
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

        # 🛡️ IMMUNE SYSTEM: Validate structural integrity of the YAML DNA
        validated_dna = proofread_global_config(raw_config)
        return validated_dna.model_dump()

    except Exception as e:
        console.print(
            f"[bold red]BOOT WARNING: Config DNA failed to load ({e}).[/bold red]"
        )
        return {"agents": {}, "routes": {}, "models": {}}


# ⚡ ZERO-DEBT: The Global Singleton
AGENT_CONFIG = _load_dna()
