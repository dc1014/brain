# --- System/core/dna.py ---
import yaml  # type: ignore
import hashlib
import json
from typing import Any
from pathlib import Path
from rich.console import Console

try:
    import jinja2
except ImportError:
    jinja2 = None  # type: ignore

from System.core.paths import ROOT_DIR

console = Console()

_cached_config: dict[str, Any] = {}
_cached_hash: str = ""

CONFIG_FILES = ["system.yaml", "agents.yaml", "tools.yaml", "routes.yaml"]
AGENTS_DIR = ROOT_DIR / "System" / "config" / "agents"


def _hash_directory(directory: Path) -> str:
    """Computes a hash of all markdown files in a directory to detect mutations."""
    hasher = hashlib.md5()
    if directory.exists():
        for filepath in sorted(directory.glob("*.md")):
            if filepath.is_file():
                with open(filepath, "rb") as f:
                    hasher.update(f.read())
    return hasher.hexdigest()


def _compute_dna_hash() -> str:
    """Computes a composite MD5 hash across the config triad and markdown agents to detect mutations."""
    hasher = hashlib.md5()

    config_dir = ROOT_DIR / "System" / "config"
    for file in CONFIG_FILES:
        filepath = config_dir / file
        if filepath.exists():
            with open(filepath, "rb") as f:
                hasher.update(f.read())

    # ⚡ Use the module-level variable so pytest can mock it
    hasher.update(_hash_directory(AGENTS_DIR).encode("utf-8"))

    return hasher.hexdigest()


def _apply_cognitive_pruning(config: dict[str, Any]) -> dict[str, Any]:
    features_path = ROOT_DIR / "System" / "config" / "features.json"
    if not features_path.exists():
        return config

    try:
        with open(features_path, "r", encoding="utf-8") as f:
            features = json.load(f)
    except Exception:
        return config

    tools = config.get("tools", {})

    feature_tool_map = {
        "vision": {"groups": ["vision"], "tool_names": []},
        "audio": {"groups": [], "tool_names": ["speak", "analyze_audio"]},
    }

    for feature_key, dependencies in feature_tool_map.items():
        feature_state = features.get(feature_key, {})
        is_enabled = feature_state.get("enabled", False)

        if not is_enabled:
            for group in dependencies.get("groups", []):
                if group in tools:
                    del tools[group]

            target_tools = set(dependencies.get("tool_names", []))
            if target_tools:
                for group_name, tool_list in tools.items():
                    if isinstance(tool_list, list):
                        tools[group_name] = [
                            t
                            for t in tool_list
                            if (
                                t.get("function", {}).get("name")
                                if isinstance(t, dict)
                                else t
                            )
                            not in target_tools
                        ]

    config["tools"] = tools

    if not features.get("autonomous_daydreaming", {}).get("enabled", False):
        target_tools = {
            "read_safe_file",
            "search_vault",
            "web_search",
            "scrape_webpage",
        }
        for agent_name, agent_data in config.get("agents", {}).items():
            if "daydream" in agent_name.lower() or "dmn" in agent_name.lower():
                if "tools" in agent_data:
                    agent_data["tools"] = [
                        t for t in agent_data["tools"] if t not in target_tools
                    ]

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

        raw_config: dict[str, Any] = {
            "agents": {},
            "tools": {},
            "_templates": {},
            "_few_shots": {},
        }

        for file in CONFIG_FILES:
            filepath = config_dir / file
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                    # ⚡ THE FIX: Explicitly nest tools.yaml under the "tools" key!
                    if file == "tools.yaml":
                        raw_config["tools"].update(data)
                    else:
                        if "agents" in data and "agents" in raw_config:
                            raw_config["agents"].update(data["agents"])
                            del data["agents"]
                        raw_config.update(data)

        if AGENTS_DIR.exists():
            for md_file in AGENTS_DIR.glob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            frontmatter = yaml.safe_load(parts[1]) or {}
                            prompt_body = parts[2].strip()
                            agent_id = md_file.stem

                            agent_data = {
                                "name": frontmatter.get("name", agent_id),
                                "model": frontmatter.get("model", "openai/gpt-4o-mini"),
                                "system_prompt": prompt_body,
                                "fallbacks": frontmatter.get("fallbacks", []),
                                "tools": frontmatter.get("tools", []),
                                "creates_milestone": frontmatter.get(
                                    "creates_milestone", True
                                ),
                                "output_schema": frontmatter.get("output_schema", None),
                            }

                            raw_config["agents"][agent_id] = agent_data

                            if jinja2:
                                raw_config["_templates"][agent_id] = jinja2.Template(
                                    prompt_body
                                )

                        except Exception as parse_e:
                            console.print(
                                f"[dim red]Failed to parse agent {md_file.name}: {parse_e}[/dim red]"
                            )

        templates = raw_config.pop("_templates", {})
        few_shots = raw_config.pop("_few_shots", {})

        validated_dna = proofread_global_config(raw_config)
        dumped_config = validated_dna.model_dump()

        dumped_config["_templates"] = templates
        dumped_config["_few_shots"] = few_shots

        # ⚡ Ensure the tools dictionary survives Pydantic validation
        if "tools" not in dumped_config and "tools" in raw_config:
            dumped_config["tools"] = raw_config["tools"]

        _cached_config = _apply_cognitive_pruning(dumped_config)
        _cached_hash = current_hash

        return _cached_config

    except Exception as e:
        console.print(
            f"[bold red]BOOT WARNING: Failed to load config triad ({e}).[/bold red]"
        )
        return {"agents": {}, "routes": {}, "models": {}, "tools": {}}
