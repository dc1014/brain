from System.core.schemas import AgentResponseSchema, MarkdownTranslator
import asyncio
import json
import litellm  # type: ignore
import os
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


def clean_json_output(text: str) -> str:
    """Strips rogue markdown backticks from native structured outputs."""
    if not text:
        return "{}"
    return text.strip("`").removeprefix("json").strip()


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
    origin: str = "HUMAN",  # Track the execution origin
) -> None:
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "origin": origin,  # ⚡ Inject it into the JSON payload
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
    from System.core.dna import get_dna_config

    roles = role_name if isinstance(role_name, list) else [role_name]

    base_prompt = system_prompt + "\n" if system_prompt else ""

    for r in roles:
        agent_data = get_dna_config().get("agents", {}).get(r.lower(), {})
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

    # 🔐 SAFE-BY-DEFAULT COGNITIVE ALIGNMENT: Tell the AI exactly why its tools are missing
    code_execution_enabled = os.environ.get(
        "BRAIN_ENABLE_CODE_EXECUTION", "false"
    ).lower() in ("true", "1", "yes")
    if not code_execution_enabled:
        base_prompt += (
            "\n\n[SYSTEM ADVISORY]: You are currently running in Safe-by-Default (Advisory) mode. "
            "You do NOT have access to code execution tools (like execute_in_sandbox or execute_command). "
            "Do not attempt to execute code. Instead, draft the final files to the workspace using your file writing tools, "
            "and clearly instruct the human user on how to run them in their terminal.\n"
        )

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

    # 2. Cortisol Resource Conservation (Model Fallback)
    final_model = base_model
    if vector["cortisol"] > 0.7:
        from System.core.dna import get_dna_config

        # Force fallback to the cheap/fast model to survive resource exhaustion
        fast_model = get_dna_config().get("models", {}).get("fast", base_model)
        if fast_model != base_model:
            final_model = fast_model
            console.print(
                "[dim magenta]🩸 Cortisol Overload: Routing to efficiency matrix.[/dim magenta]"
            )

    # 3. Hardened Dynamic Token Throttling Tiers (Cost & Stress Protection)
    # Bridge directly to EndocrineSystem to calculate tier-based token caps
    max_tokens = endocrine.calculate_token_limit(final_model)

    return final_model, final_temp, max_tokens


async def run_agent_async(
    role_name: str,
    model_string: str,
    system_prompt: str,
    user_prompt: str,
    route: str = "UNKNOWN",
    domain: str = "NONE",
    step: int = 1,
    tools: list[dict[str, Any]] | None = None,
    origin: str = "HUMAN",  # Accept the 'origin' baton from the PFC
) -> AgentResponse:
    """Invokes the active Swarm node natively asynchronously using litellm."""

    # ⚡ SHIFT-LEFT: Apply Humoral State Tuning before computation
    mod_model, mod_temp, mod_tokens = apply_humoral_modulation(model_string)

    # ⚡ SHIFT-LEFT TOKEN ECONOMICS: Ephemeral Prompt Caching
    # Anthropic allows us to cache the massive System Prompt and Tool Registry in memory.
    messages: list[dict[str, Any]] = []

    if "claude" in model_string.lower() or "anthropic" in model_string.lower():
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            },
            {"role": "user", "content": user_prompt},
        ]
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    total_prompt = 0

    total_prompt = 0
    total_comp = 0
    final_text = ""
    action_manifest: list[str] = []

    try:
        from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere
        from System.neuroanatomy.cortical.motor_cortex import execute_tools
        from System.neuroanatomy.cortical.working_memory import compress_message_array

        model_string = route_hemisphere(route, model_string)

        for iteration in range(5):
            # Dynamically compress bloated history arrays
            messages = await compress_message_array(messages, model_string)
            pruned_messages = messages

            # 🛡️ IMMUNE SYSTEM: Check the Vault
            _has_anthropic = bool(vault.get_secret("ANTHROPIC_API_KEY"))
            _has_openai = bool(vault.get_secret("OPENAI_API_KEY"))

            if (
                "anthropic" in model_string.lower()
                and not _has_anthropic
                and _has_openai
            ):
                if iteration == 0:
                    console.print(
                        "[yellow]⚠️ Anthropic key missing. Falling back to configured heavy model.[/yellow]"
                    )
                # ⚡ P1 FIX: Respect the user's heavy fallback preference from their DNA
                from System.core.dna import get_dna_config

                model_string = (
                    get_dna_config().get("models", {}).get("heavy", "openai/gpt-4o")
                )

            # 🧠 THALAMIC ROUTING: Mutate model strings and resolve auto-discovered keys
            routed_model, api_key = vault.resolve_routing(mod_model)

            # ⚡ NATIVE ASYNC API CALL
            response = await acompletion(
                model=routed_model,
                messages=pruned_messages,
                response_format=AgentResponseSchema,
                tools=tools,
                temperature=mod_temp,
                max_tokens=mod_tokens,
                api_key=api_key,
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

            # If the LLM returns our new Pydantic Schema, parse it and translate to Markdown.
            # Native Structured Outputs
            # We explicitly trust LiteLLM's response_format enforcement. No brittle regex.
            clean_json = clean_json_output(message.content or "")

            if clean_json and clean_json.startswith(("{", "[")):
                try:
                    # Natively validate via Pydantic. If the LLM hallucinated, it fails loudly.
                    parsed_schema = AgentResponseSchema.model_validate_json(clean_json)

                    # 1. Translate pure JSON back into beautiful Markdown for Obsidian logs
                    human_readable_log = MarkdownTranslator.render_agent_log(
                        parsed_schema
                    )
                    final_text += human_readable_log + "\n"

                    # 2. Store the raw JSON in the context window
                    message_dict["content"] = clean_json
                    messages.append(message_dict)

                    # 3. Synthesize the JSON tool schemas back into the format the Motor Cortex expects
                    if parsed_schema.tool_calls:
                        # --- ⚡ DELEGATE TO MOTOR CORTEX ---
                        # We pass the pure Pydantic ToolCallSchema objects natively. No adapter mocks.
                        tool_messages, new_actions, halt_text = await execute_tools(
                            parsed_schema.tool_calls,
                            role_name,
                            step_index=iteration,
                            route=route,
                        )

                        # Flatten synthetic tool results into a standard user message
                        flat_results = "Tool Execution Results:\n"
                        for tm in tool_messages:
                            content_str = tm.get("content", "")
                            # ⚡ SHIFT-LEFT TOKEN ECONOMICS: Hard Environment Ceiling
                            if len(content_str) > 15000:
                                content_str = (
                                    content_str[:15000]
                                    + "\n\n... [ ✂️ TRUNCATED: OUTPUT EXCEEDED 15,000 CHARACTERS. USE `grep`, `head`, OR `tail` ]"
                                )
                            flat_results += f"{content_str}\n"

                        messages.append(
                            {"role": "user", "content": flat_results.strip()}
                        )
                        action_manifest.extend(new_actions)

                        if halt_text:
                            final_text += halt_text
                            break
                        continue
                    else:
                        break

                except Exception as e:
                    console.print(f"[dim red]JSON Schema Parse Error: {e}[/dim red]")
                    # If it fails completely, it falls through to the legacy fallback block below!
            else:
                # 🛡️ BACKWARD COMPATIBILITY (Protects Pytest Mocks & Legacy Routes)
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

                if hasattr(message, "tool_calls") and message.tool_calls:
                    tool_messages, new_actions, halt_text = await execute_tools(
                        message.tool_calls, role_name, step_index=iteration, route=route
                    )

                    # ⚡ SHIFT-LEFT TOKEN ECONOMICS: Hard Environment Ceiling
                    for tm in tool_messages:
                        if (
                            isinstance(tm.get("content"), str)
                            and len(tm["content"]) > 15000
                        ):
                            tm["content"] = (
                                tm["content"][:15000]
                                + "\n\n... [ ✂️ TRUNCATED: OUTPUT EXCEEDED 15,000 CHARACTERS. USE `grep`, `head`, OR `tail` ]"
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
            origin,  # Pass the baton to the logger!
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
            origin,  # Pass the baton to the logger!
        )
        return AgentResponse(text=error_msg, actions=action_manifest, usage=usage_data)
