import json
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


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
        ..., description="The standard output or execution result string."
    )
    block_reason: Optional[str] = None

    def __bool__(self) -> bool:
        return self.success

    def __str__(self) -> str:
        return self.output

    def __contains__(self, item: object) -> bool:
        return str(item) in self.output

    def strip(self) -> str:
        return self.output.strip()


class WebhookConfig(BaseModel):
    route_name: str = Field(
        ..., description="The URL path endpoint (e.g., 'github_push')"
    )
    secret_env_var: str = Field(
        ..., description="The local environment variable holding the HMAC secret"
    )
    signature_header: str = Field(
        ..., description="The HTTP header containing the cryptographic signature"
    )
    payload_mapping: dict[str, str] = Field(
        ..., description="Dot-notation mapping to extract text fields"
    )
    target_action: str = Field(
        ..., description="Spinal route: 'reflex', 'visceral', or 'exteroceptive'"
    )
    template: str = Field(
        ..., description="The token-optimized string template to send to the Spine"
    )


class DaemonConfig(BaseModel):
    enabled: bool
    polling_throttle_ms: int = 1000
    targets: list[str] = []
    secure_port: int = 8080
    auto_tunnel_on_wake: bool = False


class CircadianConfig(BaseModel):
    sleep_interval_minutes: int = 120
    deep_sleep_enabled: bool = True


class ToolCallSchema(BaseModel):
    model_config = {"extra": "forbid"}

    tool_name: str

    # Anthropic strictly rejects open-ended 'dict' objects.
    # Force the LLM to output a JSON-formatted string instead.
    parameters: str = Field(
        default="{}",
        description="A JSON-formatted string containing the exact arguments for the tool.",
    )

    reasoning: Optional[str] = None
    id: Optional[str] = None


class AgentResponseSchema(BaseModel):
    # Ensure the root response wrapper also satisfies Anthropic's strictness
    model_config = {"extra": "forbid"}

    thought_process: str

    tool_calls: Optional[List[ToolCallSchema]] = Field(default_factory=list)

    final_response: Optional[str] = Field(
        None, description="The final text to show the user if no tools are needed."
    )


class EpiphanySchema(BaseModel):
    """The structured output for the Default Mode Network (DMN) daydreams."""

    title: str = Field(
        ..., description="A short, poetic title for the technical epiphany."
    )
    technical_summary: str = Field(
        ..., description="The core technical realization or optimization."
    )
    actionable_steps: List[str] = Field(
        ..., description="Specific commands or architectural changes to implement."
    )


# =====================================================================
# THE OBSIDIAN TRANSLATION LAYER (JSON -> Markdown Bridge)
# =====================================================================


class MarkdownTranslator:
    """Compiles strict JSON structured outputs back into beautiful Obsidian Markdown."""

    @staticmethod
    def render_epiphany(epiphany: EpiphanySchema) -> str:
        """Converts a JSON Epiphany into a beautiful Markdown block for daydreams.md"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = f"## 🌌 Epiphany ({timestamp}) - {epiphany.title}\n\n"
        md += f"**Realization:**\n{epiphany.technical_summary}\n\n"

        if epiphany.actionable_steps:
            md += "**Proposed Synaptic Routing (Next Steps):**\n"
            for step in epiphany.actionable_steps:
                md += f"- {step}\n"

        md += "\n---\n"
        return md

    @staticmethod
    def render_agent_log(response: AgentResponseSchema) -> str:
        """Converts standard agent JSON actions into a readable log format."""
        md = f"> **Thought:** {response.thought_process}\n\n"

        if response.tool_calls:
            md += "**Actions:**\n"
            for call in response.tool_calls:
                param_str = ""
                if isinstance(call.parameters, str):
                    try:
                        parsed_json = json.loads(call.parameters)
                        param_str = json.dumps(parsed_json, indent=2)
                    except Exception:
                        param_str = call.parameters
                else:
                    param_str = json.dumps(call.parameters, indent=2)

                md += f"- `[ {call.tool_name} ]`\n```json\n{param_str}\n```\n"

        if response.final_response:
            md += f"\n**Response:**\n{response.final_response}\n"

        return md
