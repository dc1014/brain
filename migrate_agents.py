import re
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
CONFIG_DIR = ROOT / "System" / "config"
OLD_YAML = CONFIG_DIR / "agents.yaml"


def execute_dna_split():
    print("🧬 Initiating DNA Split (Models, Agents, Routes)...")
    content = OLD_YAML.read_text(encoding="utf-8")

    # 1. Safely extract the three blocks using Regex
    models_match = re.search(
        r"^(models:.*?)^\s*agents:", content, flags=re.MULTILINE | re.DOTALL
    )
    agents_match = re.search(
        r"^(agents:.*?)^\s*routes:", content, flags=re.MULTILINE | re.DOTALL
    )
    routes_match = re.search(r"^(routes:.*)", content, flags=re.MULTILINE | re.DOTALL)

    if not (models_match and agents_match and routes_match):
        print("❌ Failed to parse YAML structure. Aborting.")
        return

    # Write the 3 new configuration files
    (CONFIG_DIR / "models.yaml").write_text(
        models_match.group(1).strip() + "\n", encoding="utf-8"
    )
    (CONFIG_DIR / "agents.yaml").write_text(
        agents_match.group(1).strip() + "\n", encoding="utf-8"
    )
    (CONFIG_DIR / "routes.yaml").write_text(
        routes_match.group(1).strip() + "\n", encoding="utf-8"
    )
    print("✅ Split DNA into models.yaml, agents.yaml, and routes.yaml")

    # 2. Patch Polymerase to validate all 3 files simultaneously
    poly_path = ROOT / "System" / "neuroanatomy" / "pathways" / "polymerase.py"
    poly_code = '''import yaml  # type: ignore
from pathlib import Path

class PolymeraseError(Exception):
    pass

def proofread_yaml_dna(config_dir: str | Path) -> bool:
    """DNA Polymerase: Proofreads the fragmented DNA (models, agents, routes)."""
    config_dir = Path(config_dir).resolve()
    models_file = config_dir / "models.yaml"
    agents_file = config_dir / "agents.yaml"
    routes_file = config_dir / "routes.yaml"

    for f in [models_file, agents_file, routes_file]:
        if not f.exists():
            raise PolymeraseError(f"Critical System File Missing: {f.name}")

    try:
        with open(models_file, "r", encoding="utf-8") as f:
            models_cfg = yaml.safe_load(f) or {}
        with open(agents_file, "r", encoding="utf-8") as f:
            agents_cfg = yaml.safe_load(f) or {}
        with open(routes_file, "r", encoding="utf-8") as f:
            routes_cfg = yaml.safe_load(f) or {}
    except Exception as e:
        raise PolymeraseError(f"YAML Syntax Error: {e}")

    if "models" not in models_cfg or not isinstance(models_cfg["models"], dict):
        raise PolymeraseError("models.yaml is missing required key: 'models'")

    if "agents" not in agents_cfg or not isinstance(agents_cfg["agents"], dict):
        raise PolymeraseError("agents.yaml is missing required key: 'agents'")

    for agent_id, agent_data in agents_cfg["agents"].items():
        if "name" not in agent_data: raise PolymeraseError(f"Agent '{agent_id}' missing 'name'.")
        if "model" not in agent_data: raise PolymeraseError(f"Agent '{agent_id}' missing 'model'.")
        if "system_prompt" not in agent_data: raise PolymeraseError(f"Agent '{agent_id}' missing 'system_prompt'.")
        if agent_data["model"] not in models_cfg["models"]:
            raise PolymeraseError(f"Agent '{agent_id}' references an unknown model: '{agent_data['model']}'.")

    if "routes" not in routes_cfg or not isinstance(routes_cfg["routes"], dict):
        raise PolymeraseError("routes.yaml is missing required key: 'routes'")

    for route_id, route_data in routes_cfg["routes"].items():
        if not isinstance(route_data, list):
            raise PolymeraseError(f"Route '{route_id}' must be a list.")
        for step_idx, step in enumerate(route_data):
            if "swarm" in step:
                if not isinstance(step["swarm"], list):
                    raise PolymeraseError(f"Swarm in route '{route_id}' step {step_idx} must be a list.")
            elif "agent" in step:
                if step["agent"] not in agents_cfg["agents"]:
                    raise PolymeraseError(f"Route '{route_id}' step {step_idx} references undefined agent '{step['agent']}'.")
            else:
                raise PolymeraseError(f"Route '{route_id}' step {step_idx} must define either 'agent' or 'swarm'.")

    return True
'''
    poly_path.write_text(poly_code, encoding="utf-8")
    print("✅ Polymerase Organ Upgraded.")

    # 3. Patch OS Bootloader (Runtime)
    runtime_path = ROOT / "System" / "runtime.py"
    runtime_code = runtime_path.read_text(encoding="utf-8")

    runtime_code = re.sub(
        r"from System\.neuroanatomy\.pathways\.polymerase import proofread_agents_yaml, PolymeraseError",
        "from System.neuroanatomy.pathways.polymerase import proofread_yaml_dna, PolymeraseError",
        runtime_code,
    )

    runtime_loader = """CONFIG_DIR = ROOT_DIR / "System" / "config"
try:
    # 🧬 DNA POLYMERASE: Proofread the OS genetic code before booting
    proofread_yaml_dna(CONFIG_DIR)
    AGENT_CONFIG = {}
    for file in ["models.yaml", "agents.yaml", "routes.yaml"]:
        with open(CONFIG_DIR / file, "r", encoding="utf-8") as f:
            AGENT_CONFIG.update(yaml.safe_load(f))
except Exception as e:
    console.print(f"[bold red]BOOT WARNING: Config failed to load ({e}).[/bold red]")
    AGENT_CONFIG = {"agents": {}, "routes": {}, "models": {}}"""

    runtime_code = re.sub(
        r'CONFIG_PATH = .*?AGENT_CONFIG = \{"agents": \{\}, "routes": \{\}, "models": \{\}\}',
        runtime_loader,
        runtime_code,
        flags=re.DOTALL,
    )
    runtime_path.write_text(runtime_code, encoding="utf-8")

    # 4. Patch CLI Bootloader
    cli_path = ROOT / "System" / "cli.py"
    cli_code = cli_path.read_text(encoding="utf-8")

    cli_loader = """CONFIG_DIR = Path(__file__).parent / "config"
try:
    AGENT_CONFIG = {}
    for filename in ["models.yaml", "agents.yaml", "routes.yaml"]:
        with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
            AGENT_CONFIG.update(yaml.safe_load(f))
except Exception as e:
    console.print(f"[bold red]Fatal Error loading agents.yaml:[/bold red] {e}")
    exit(1)"""

    cli_code = re.sub(
        r'CONFIG_PATH = Path\(__file__\)\.parent / "config" / "agents\.yaml".*?exit\(1\)',
        cli_loader,
        cli_code,
        flags=re.DOTALL,
    )
    cli_path.write_text(cli_code, encoding="utf-8")

    # 5. Patch Tests
    test_path = ROOT / "System" / "tests" / "pathways" / "test_polymerase.py"
    test_code = """import pytest
import yaml
from pathlib import Path
from System.neuroanatomy.pathways.polymerase import proofread_yaml_dna, PolymeraseError

def test_polymerase_validates_healthy_dna(tmp_path: Path):
    (tmp_path / "models.yaml").write_text("models:\\n  m1: 'gpt-4'", encoding="utf-8")
    (tmp_path / "agents.yaml").write_text("agents:\\n  a1:\\n    name: 'Agent'\\n    model: 'm1'\\n    system_prompt: 'prompt'", encoding="utf-8")
    (tmp_path / "routes.yaml").write_text("routes:\\n  FAST:\\n    - agent: 'a1'\\n      tools: []\\n      context: []", encoding="utf-8")
    assert proofread_yaml_dna(tmp_path) is True

def test_polymerase_catches_missing_files(tmp_path: Path):
    with pytest.raises(PolymeraseError, match="Missing"):
        proofread_yaml_dna(tmp_path)

def test_polymerase_catches_invalid_model(tmp_path: Path):
    (tmp_path / "models.yaml").write_text("models:\\n  m1: 'gpt-4'", encoding="utf-8")
    (tmp_path / "agents.yaml").write_text("agents:\\n  a1:\\n    name: 'Agent'\\n    model: 'unknown'\\n    system_prompt: 'prompt'", encoding="utf-8")
    (tmp_path / "routes.yaml").write_text("routes:\\n  FAST:\\n    - agent: 'a1'\\n      tools: []\\n      context: []", encoding="utf-8")
    with pytest.raises(PolymeraseError, match="unknown model"):
        proofread_yaml_dna(tmp_path)
"""
    test_path.write_text(test_code, encoding="utf-8")
    print("✅ OS Bootloaders & Tests Upgraded.")


if __name__ == "__main__":
    execute_dna_split()
