from typing import Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict


class AgentNodeConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    model: str
    system_prompt: str
    tools: List[Any] = Field(default_factory=list)


class BrainDNAConfig(BaseModel):
    """
    Type-Safe Brain Configuration Matrix.
    Provides strict structural proofreading for global configuration state.
    """

    model_config = ConfigDict(extra="allow")

    models: Dict[str, str] = Field(default_factory=dict)
    agents: Dict[str, AgentNodeConfig] = Field(default_factory=dict)
    routes: Dict[str, List[Any]] = Field(default_factory=dict)


def proofread_global_config(raw_config_dict: Dict[str, Any]) -> BrainDNAConfig:
    """Validates configuration properties at system startup to prevent silent fallbacks."""
    try:
        return BrainDNAConfig.model_validate(raw_config_dict)
    except Exception as e:
        raise ValueError(
            f"🧬 Catastrophic Configuration DNA Defect Detected:\n{str(e)}"
        )
