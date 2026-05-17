import asyncio
import json
import litellm  # type: ignore
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.neuroanatomy.systemic.immune_system import vault
from System.neuroanatomy.systemic.endocrine import EndocrineSystem

from litellm import acompletion  # type: ignore

litellm.telemetry = False
litellm.drop_params = True

console = Console()

LOG_DIR: Path = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE: Path = LOG_DIR / "agent_interactions.jsonl"


@dataclass
class AgentResponse:
    text: str
    actions: list[str] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)


async def log_interaction(
    role_name: str,
    model_string: str,
    system_prompt: str,
    user_prompt: str,
    response_content: str,
    usage: dict[str, int],
    route: str = "UNKNOWN",
    domain: str = "NONE",
) -> None:
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "route": route,
        "domain": domain,
        "agent": role_name,
        "model": model_string,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "response": response_content,
        "tokens": usage,
    }

    # Secure the Motor Cortex lock for the shared log file
    from System.neuroanatomy.cortical.motor_cortex import MotorCortex

    async with MotorCortex.get_lock(LOG_FILE):

        def _write():
            # 🛡️ IMMUNE SYSTEM: Final Outbound Efferent Scrubbing for JSON logs
            raw_json = json.dumps(log_entry, default=str)
            safe_json = vault.mask_secrets(raw_json)
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(safe_json + "\n")

        await asyncio.to_thread(_write)


def get_system_context(
    role_name: str | list[str], system_prompt: str = "", prompt: str = "", **kwargs
) -> str:
    """Generates the absolute biological reality for the active Swarm agent(s)."""
    from System.core.dna import AGENT_CONFIG

    roles = role_name if isinstance(role_name, list) else [role_name]

    base_prompt = system_prompt + "\n" if system_prompt else ""

    for r in roles:
        agent_data = AGENT_CONFIG.get("agents", {}).get(r.lower(), {})
        base_prompt += (
            agent_data.get("system_prompt", f"You are the {r} node of Brain OS.") + "\n"
        )

    if prompt:
        base_prompt += f"\n{prompt}\n"

    # ⚡ SHIFT-LEFT: Retrieve dynamically learned life lessons and inject them into the AI's DNA
    try:
        from System.neuroanatomy.limbic.nucleus_accumbens import get_plasticity_rules

        plasticity = get_plasticity_rules()
        if plasticity:
            base_prompt += (
                f"\n\nCRITICAL LEARNED BEHAVIORS (From Past Failures):\n{plasticity}\n"
            )
    except ImportError:
        pass  # Failsafe in case the Limbic system is temporarily offline

    return base_prompt.strip()


def apply_humoral_modulation(base_model: str) -> tuple[str, float, int]:
    """
    Applies the continuous float vector from the Endocrine System to bias
    temperature, model routing, and token limits dynamically.
    """
    endocrine = EndocrineSystem()
    vector = endocrine.get_humoral_vector()

    # 1. Temperature Modulation (Creativity vs. Determinism)
    # Base is 0.5. Dopamine raises it. Cortisol makes it cold and calculating.
    temp = 0.5 + (vector["dopamine"] * 0.4) - (vector["cortisol"] * 0.4)
    final_temp = max(0.0, min(1.0, temp))

    # 2. Adrenaline Token Constriction
    # If Adrenaline is high (crisis), max output drops to force concise, rapid code
    max_tokens = 4000
    if vector["adrenaline"] > 0.5:
        max_tokens = int(
            max_tokens * (1.0 - (vector["adrenaline"] * 0.6))
        )  # Drops to ~1600

    # 3. Cortisol Resource Conservation (Model Fallback)
    final_model = base_model
    if vector["cortisol"] > 0.7:
        from System.runtime import AGENT_CONFIG

        # Force fallback to the cheap/fast model to survive resource exhaustion
        fast_model = AGENT_CONFIG.get("models", {}).get("fast", base_model)
        if fast_model != base_model:
            final_model = fast_model
            console.print(
                "[dim magenta]🩸 Cortisol Overload: Routing to efficiency matrix.[/dim magenta]"
            )

    return final_model, final_temp, max_tokens


async def run_agent_async(
    role_name: str,
    model_string: str,
    system_prompt: str,
    user_prompt: str,
    route: str = "UNKNOWN",
    domain: str = "NONE",
    step: int = 1,
    tools: list[dict[str, Any]] | None = None,  # ⚡ ZERO-DEBT: Restored tools parameter
) -> AgentResponse:
    """Invokes the active Swarm node natively asynchronously using litellm."""

    # ⚡ SHIFT-LEFT: Apply Humoral State Tuning before computation
    mod_model, mod_temp, mod_tokens = apply_humoral_modulation(model_string)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    total_prompt = 0
    total_comp = 0
    final_text = ""
    action_manifest: list[str] = []  # ⚡ ZERO-DEBT: Restored explicit type hint

    try:
        from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere
        from System.neuroanatomy.cortical.motor_cortex import execute_tools

        model_string = route_hemisphere(route, model_string)

        for step in range(15):
            if len(messages) > 7:
                window = messages[-5:]
                while window and window[0].get("role") == "tool":
                    window.pop(0)
                pruned_messages = [messages[0], messages[1]] + window
            else:
                pruned_messages = messages

            # 🛡️ IMMUNE SYSTEM: Check the Vault
            _has_anthropic = bool(
                vault.get_api_key_for_model("anthropic/claude-3-haiku")
            )
            _has_openai = bool(vault.get_api_key_for_model("openai/gpt-4o-mini"))

            if (
                "anthropic" in model_string.lower()
                and not _has_anthropic
                and _has_openai
            ):
                if step == 0:
                    console.print(
                        "[yellow]⚠️ Anthropic key missing. Falling back to OpenAI.[/yellow]"
                    )
                model_string = "openai/gpt-4o"

            # ⚡ NATIVE ASYNC API CALL
            response = await acompletion(
                model=mod_model,
                messages=pruned_messages,  # ⚡ ZERO-DEBT: Prevents context window explosion
                tools=tools,
                temperature=mod_temp,
                max_tokens=mod_tokens,
            )

            if not getattr(response, "choices", None) or len(response.choices) == 0:
                return AgentResponse(
                    text="API SECURITY BLOCK: Empty response.", actions=action_manifest
                )

            message = response.choices[0].message

            if hasattr(response, "usage") and response.usage:
                total_prompt += int(getattr(response.usage, "prompt_tokens", 0))
                total_comp += int(getattr(response.usage, "completion_tokens", 0))

            message_dict: dict[str, Any] = {"role": "assistant"}
            if message.content:
                message_dict["content"] = message.content
                final_text += str(message.content) + "\n"

            if hasattr(message, "tool_calls") and message.tool_calls:
                processed_tools = [
                    t.model_dump() if hasattr(t, "model_dump") else t
                    for t in message.tool_calls
                ]
                message_dict["tool_calls"] = processed_tools

            messages.append(message_dict)

            # --- ⚡ DELEGATE TO MOTOR CORTEX ---
            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_messages, new_actions, halt_text = await execute_tools(
                    message.tool_calls, role_name, step_index=step
                )

                messages.extend(tool_messages)
                action_manifest.extend(new_actions)

                if halt_text:
                    final_text += halt_text
                    break
                continue
            else:
                break

        usage_data = {
            "prompt_tokens": total_prompt,
            "completion_tokens": total_comp,
            "total_tokens": total_prompt + total_comp,
        }

        # 🛡️ IMMUNE SYSTEM: Scrub the LLM payload before it reaches the OS or Console
        safe_final_text = vault.mask_secrets(final_text.strip())
        safe_action_manifest = [vault.mask_secrets(a) for a in action_manifest]

        await log_interaction(
            role_name,
            model_string,
            system_prompt,
            user_prompt,
            safe_final_text + "\n\nACTIONS:\n" + "\n".join(safe_action_manifest),
            usage_data,
            route,
            domain,
        )
        return AgentResponse(
            text=safe_final_text, actions=safe_action_manifest, usage=usage_data
        )

    except Exception as e:
        # 🛡️ IMMUNE SYSTEM: Scrub Python exception traces
        error_msg = vault.mask_secrets(f"API/Execution Error: {str(e)}")
        usage_data = {
            "prompt_tokens": total_prompt,
            "completion_tokens": total_comp,
            "total_tokens": total_prompt + total_comp,
        }
        await log_interaction(
            role_name,
            model_string,
            system_prompt,
            user_prompt,
            error_msg,
            usage_data,
            route,
            domain,
        )
        return AgentResponse(text=error_msg, actions=action_manifest, usage=usage_data)
