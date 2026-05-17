import pytest
from System.core.config_proofreader import proofread_global_config, BrainDNAConfig


def test_proofreader_valid_config():
    raw_config = {
        "models": {"fast": "gemini-flash"},
        "agents": {
            "test_agent": {
                "name": "Test",
                "model": "fast",
                "system_prompt": "You are a test.",
            }
        },
        "routes": {"TEST_ROUTE": []},
    }
    validated = proofread_global_config(raw_config)
    assert isinstance(validated, BrainDNAConfig)
    assert validated.agents["test_agent"].name == "Test"


def test_proofreader_invalid_agent_config():
    raw_config = {
        "agents": {
            "bad_agent": {
                "name": "Bad",
                # Missing 'model' and 'system_prompt'
            }
        }
    }
    with pytest.raises(ValueError, match="Catastrophic Configuration DNA Defect"):
        proofread_global_config(raw_config)
