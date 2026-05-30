import yaml  # type: ignore
import hashlib
import json
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


def _apply_cognitive_pruning(config: dict[str, Any]) -> dict[str, Any]:
    """
    SHIFT-LEFT FEATURE FLAGGING:
    Dynamically strips tools from the LLM's context window if the underlying
    sensory organs or features are disabled in features.json.
    """
    features_path = ROOT_DIR / "System" / "config" / "features.json"
    if not features_path.exists():
        return config

    try:
        with open(features_path, "r", encoding="utf-8") as f:
            features = json.load(f)
    except Exception:
        return config

    tools = config.get("tools", {})

    # Extensible Registry: Map feature flags to tool groups or specific isolated tools
    feature_tool_map = {
        "vision": {
            "groups": ["vision"],  # Drops the entire 'vision' group from tools.yaml
            "tool_names": [],
        },
        "audio": {
            "groups": [],
            "tool_names": [
                "speak",
                "analyze_audio",
            ],  # Drops specific tools across any group
        },
    }

    for feature_key, dependencies in feature_tool_map.items():
        feature_state = features.get(feature_key, {})
        is_enabled = feature_state.get("enabled", False)

        if not is_enabled:
            # 1. Prune entire tool groups (e.g., dropping all 'vision' tools)
            for group in dependencies.get("groups", []):
                if group in tools:
                    del tools[group]

            # 2. Prune specific isolated tools (e.g., dropping 'speak' from the 'base' group)
            target_tools = set(dependencies.get("tool_names", []))
            if target_tools:
                for group_name, tool_list in tools.items():
                    if isinstance(tool_list, list):
                        tools[group_name] = [
                            t
                            for t in tool_list
                            if t.get("function", {}).get("name") not in target_tools
                        ]

    config["tools"] = tools
    return config


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
        dumped_config = validated_dna.model_dump()

        # Apply strict feature flagging before caching
        _cached_config = _apply_cognitive_pruning(dumped_config)
        _cached_hash = current_hash

        return _cached_config

    except Exception as e:
        console.print(
            f"[bold red]BOOT WARNING: Failed to load config triad ({e}).[/bold red]"
        )
        return {"agents": {}, "routes": {}, "models": {}, "tools": {}}
