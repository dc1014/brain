import pytest
from System.organs.polymerase import proofread_agents_yaml, PolymeraseError


def test_polymerase_valid_config(tmp_path):
    valid_yaml = """
models:
  fast: "openai/gpt-4o-mini"
agents:
  tester:
    name: "Tester"
    model: "fast"
    system_prompt: "You are a test."
routes:
  TEST_ROUTE:
    - agent: "tester"
      tools: ["base"]
      context: ["Meta"]
    """
    config_path = tmp_path / "agents.yaml"
    config_path.write_text(valid_yaml)

    assert proofread_agents_yaml(config_path) is True


def test_polymerase_catches_typos(tmp_path):
    invalid_yaml = """
models:
  fast: "openai/gpt-4o-mini"
agents:
  tester:
    name: "Tester"
    model: "fast"
    system_promtp: "TYPO HERE"  # Typo!
pipelines:
  TEST_ROUTE:
    - agent: "tester"
      tools: ["base"]
      context: ["Meta"]
    """
    config_path = tmp_path / "agents.yaml"
    config_path.write_text(invalid_yaml)

    with pytest.raises(PolymeraseError, match="missing a 'system_prompt'"):
        proofread_agents_yaml(config_path)


def test_polymerase_catches_missing_agent_reference(tmp_path):
    invalid_yaml = """
models:
  fast: "openai/gpt-4o-mini"
agents:
  tester:
    name: "Tester"
    model: "fast"
    system_prompt: "I exist."
routes:
  TEST_ROUTE:
    - agent: "ghost"  # References an agent that doesn't exist!
      tools: ["base"]
      context: ["Meta"]
    """
    config_path = tmp_path / "agents.yaml"
    config_path.write_text(invalid_yaml)

    with pytest.raises(PolymeraseError, match="references undefined agent 'ghost'"):
        proofread_agents_yaml(config_path)
