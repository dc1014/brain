import yaml  # type: ignore
from pathlib import Path


class PolymeraseError(Exception):
    pass


def proofread_yaml_dna(config_dir: str | Path) -> bool:
    """DNA Polymerase: Proofreads the fragmented DNA (models, agents, routes)."""
    config_dir_path = Path(config_dir).resolve()
    models_file = config_dir_path / "models.yaml"
    agents_file = config_dir_path / "agents.yaml"
    routes_file = config_dir_path / "routes.yaml"

    for config_file in [models_file, agents_file, routes_file]:
        if not config_file.exists():
            raise PolymeraseError(f"Critical System File Missing: {config_file.name}")

    try:
        with open(models_file, "r", encoding="utf-8") as file:
            models_cfg = yaml.safe_load(file) or {}
        with open(agents_file, "r", encoding="utf-8") as file:
            agents_cfg = yaml.safe_load(file) or {}
        with open(routes_file, "r", encoding="utf-8") as file:
            routes_cfg = yaml.safe_load(file) or {}
    except Exception as e:
        raise PolymeraseError(f"YAML Syntax Error: {e}")

    if "models" not in models_cfg or not isinstance(models_cfg["models"], dict):
        raise PolymeraseError("models.yaml is missing required key: 'models'")

    if "agents" not in agents_cfg or not isinstance(agents_cfg["agents"], dict):
        raise PolymeraseError("agents.yaml is missing required key: 'agents'")

    for agent_id, agent_data in agents_cfg["agents"].items():
        if "name" not in agent_data:
            raise PolymeraseError(f"Agent '{agent_id}' missing 'name'.")
        if "model" not in agent_data:
            raise PolymeraseError(f"Agent '{agent_id}' missing 'model'.")
        if "system_prompt" not in agent_data:
            raise PolymeraseError(f"Agent '{agent_id}' missing 'system_prompt'.")
        if agent_data["model"] not in models_cfg["models"]:
            raise PolymeraseError(
                f"Agent '{agent_id}' references an unknown model: '{agent_data['model']}'."
            )

    if "routes" not in routes_cfg or not isinstance(routes_cfg["routes"], dict):
        raise PolymeraseError("routes.yaml is missing required key: 'routes'")

    for route_id, route_data in routes_cfg["routes"].items():
        if not isinstance(route_data, list):
            raise PolymeraseError(f"Route '{route_id}' must be a list.")
        for step_idx, step in enumerate(route_data):
            if "swarm" in step:
                if not isinstance(step["swarm"], list):
                    raise PolymeraseError(
                        f"Swarm in route '{route_id}' step {step_idx} must be a list."
                    )
            elif "agent" in step:
                if step["agent"] not in agents_cfg["agents"]:
                    raise PolymeraseError(
                        f"Route '{route_id}' step {step_idx} references undefined agent '{step['agent']}'."
                    )
            else:
                raise PolymeraseError(
                    f"Route '{route_id}' step {step_idx} must define either 'agent' or 'swarm'."
                )

    return True
