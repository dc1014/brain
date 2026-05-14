from pydantic import BaseModel, Field


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
