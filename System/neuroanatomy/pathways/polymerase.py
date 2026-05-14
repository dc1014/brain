import yaml  # type: ignore
from pathlib import Path


class PolymeraseError(Exception):
    """Raised when the DNA Polymerase detects a malformed configuration sequence."""

    pass


def proofread_agents_yaml(yaml_path: str | Path) -> bool:
    """
    DNA Polymerase: Proofreads the core agents.yaml configuration.
    Shift-Left: Fails instantly at boot if the configuration is malformed.
    """
    path = Path(yaml_path).resolve()
    if not path.exists():
        raise PolymeraseError(f"Critical System File Missing: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise PolymeraseError(f"YAML Syntax Error in {path.name}: {e}")

    if not isinstance(config, dict):
        raise PolymeraseError(f"Root of {path.name} must be a dictionary.")

    # 1. Validate Models Array
    if "models" not in config or not isinstance(config["models"], dict):
        raise PolymeraseError("Missing or invalid required key: 'models'")

    # 2. Validate Agent Definitions
    if "agents" not in config or not isinstance(config["agents"], dict):
        raise PolymeraseError("Missing or invalid required key: 'agents'")

    for agent_id, agent_data in config["agents"].items():
        if "name" not in agent_data:
            raise PolymeraseError(f"Agent '{agent_id}' is missing a 'name'.")
        if "model" not in agent_data:
            raise PolymeraseError(f"Agent '{agent_id}' is missing a 'model'.")
        if "system_prompt" not in agent_data:
            raise PolymeraseError(f"Agent '{agent_id}' is missing a 'system_prompt'.")
        if agent_data["model"] not in config["models"]:
            raise PolymeraseError(
                f"Agent '{agent_id}' references an unknown model: '{agent_data['model']}'."
            )

    # 3. Validate Routing Pathways (Corrected to 'routes')
    if "routes" not in config or not isinstance(config["routes"], dict):
        raise PolymeraseError("Missing or invalid required key: 'routes'")

    for route_id, route_data in config["routes"].items():
        if not isinstance(route_data, list):
            raise PolymeraseError(
                f"Route '{route_id}' must be a list of execution steps."
            )

        for step_idx, step in enumerate(route_data):
            if "swarm" in step:
                if not isinstance(step["swarm"], list):
                    raise PolymeraseError(
                        f"Swarm in route '{route_id}' step {step_idx} must be a list."
                    )
            elif "agent" in step:
                if step["agent"] not in config["agents"]:
                    raise PolymeraseError(
                        f"Route '{route_id}' step {step_idx} references undefined agent '{step['agent']}'."
                    )
                if "tools" not in step or not isinstance(step["tools"], list):
                    raise PolymeraseError(
                        f"Route '{route_id}' step {step_idx} is missing a valid 'tools' array."
                    )
                if "context" not in step or not isinstance(step["context"], list):
                    raise PolymeraseError(
                        f"Route '{route_id}' step {step_idx} is missing a valid 'context' array."
                    )
            else:
                raise PolymeraseError(
                    f"Route '{route_id}' step {step_idx} must define either 'agent' or 'swarm'."
                )

    return True
