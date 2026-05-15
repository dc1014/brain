from pydantic import BaseModel, Field
from typing import Optional


class NeuroplasticityRule(BaseModel):
    agent: str = Field(..., description="The target agent name")
    rule: str = Field(..., description="The new rule to follow")


class SleepConsolidation(BaseModel):
    sleep_summary: str = Field(
        ..., description="A brief text summary of what was consolidated."
    )
    neuroplasticity: list[NeuroplasticityRule] = Field(default_factory=list)
    updated_memory: str = Field(
        ..., description="The COMPLETE, fully updated markdown file content."
    )


class QAAuditResult(BaseModel):
    audit_result: str = Field(..., description="EXACTLY 'PASS' or 'FAIL'")
    reasoning: str = Field(..., description="Explanation of critique or approval")


class DispatcherResult(BaseModel):
    reasoning: str = Field(
        ..., description="Explain step-by-step why this route and domain were selected."
    )
    route: str = Field(
        ..., description="The designated pipeline route (e.g., FORGE, FAST, SENSE)."
    )
    domain: str = Field(
        ..., description="The designated domain context (e.g., STUDIO, MEDIA)."
    )


class ExecutionResult(BaseModel):
    success: bool = Field(
        ..., description="True if execution succeeded, False if blocked or failed."
    )
    output: str = Field(
        ..., description="The stdout/stderr or return message to pass back to the LLM."
    )

    # 🎯 FIX 1: Satisfies MyPy's strict "Missing named argument" error
    block_reason: Optional[str] = None

    # 🎯 FIX 2: Polyfills for backwards compatibility with legacy string operations!
    # This allows old tests to magically check if strings are "in" the Dataclass!
    def __contains__(self, item: object) -> bool:
        return str(item) in self.output

    # 🎯 FIX 3: Teaches the Dataclass how to .strip() itself for the Somatosensory organ!
    def strip(self) -> str:
        return self.output.strip()
