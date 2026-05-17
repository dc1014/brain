import pytest
from System.core.config_proofreader import proofread_global_config, BrainDNAConfig


def test_proofreader_valid_config():
    raw = {
        "models": {"fast": "flash"},
        "agents": {
            "test": {
                "name": "Test",
                "model": "fast",
                "system_prompt": "hello",
                "creates_milestone": False,
            }
        },
        "routes": {"A": []},
    }
    validated = proofread_global_config(raw)
    assert isinstance(validated, BrainDNAConfig)
    assert (
        validated.agents["test"].model_config.get("extra") == "allow"
    )  # Ensures extra fields don't break it


def test_proofreader_invalid_config():
    with pytest.raises(ValueError, match="Catastrophic Configuration DNA"):
        proofread_global_config({"agents": {"bad": {"name": "Bad"}}})  # Missing 'model'
