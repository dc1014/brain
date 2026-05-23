from System.core.schemas import AgentResponseSchema, MarkdownTranslator, ToolCallSchema
import asyncio
import json
import litellm  # type: ignore
import re
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


def extract_json_from_text(text: str) -> str:
    """Robustly extracts a JSON block from LLM output, bypassing Markdown UI bugs."""
    if not text:
        return ""

    # Generate backticks dynamically so Markdown parsers don't crash
    bt = chr(96) * 3
    pattern = bt + r"(?:json)?\s*(\{.*?\})\s*" + bt

    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start : end + 1]
    return text


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
    origin: str = "HUMAN",  # ⚡ THE FIX: Track the execution origin
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

    schema_dict = {
        "thought_process": "Your internal reasoning and planning.",
        "tool_calls": [
            {
                "tool_name": "exact_name_of_tool_to_run",
                "parameters": {"arg1": "value1"},
                "reasoning": "Why you need this tool.",
            }
        ],
        "final_response": "Your final text to the user. MUST be a string if task is complete. Null if executing tools.",
    }

    base_prompt += (
        "\nCRITICAL PROTOCOL - STRUCTURED OUTPUT REQUIRED:\n"
        "1. You MUST output your ENTIRE response as a single, valid JSON object.\n"
        "2. Do NOT wrap it in markdown block quotes.\n"
        "3. HALT CONDITION: If you have finished the task or want to stop, you MUST pass an empty array [] for 'tool_calls' and provide a 'final_response'.\n"
        "4. DO NOT hallucinate fake tools like 'verification_complete'. Only use tools explicitly provided to you.\n"
        "Your output MUST perfectly match this JSON schema:\n"
        f"{json.dumps(schema_dict, indent=2)}\n"
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
    # ⚡ THE FIX: Bridge directly to EndocrineSystem to calculate tier-based token caps
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
    origin: str = "HUMAN",  # ⚡ THE FIX: Accept the 'origin' baton from the PFC
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
    action_manifest: list[str] = []

    try:
        from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere
        from System.neuroanatomy.cortical.motor_cortex import execute_tools

        model_string = route_hemisphere(route, model_string)

        for iteration in range(5):
            if len(messages) > 7:
                window = messages[-5:]
                while window and window[0].get("role") == "tool":
                    window.pop(0)
                pruned_messages = [messages[0], messages[1]] + window
            else:
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
            # ⚡ ZERO-DEBT: HYBRID PARSING BRIDGE (WITH SELF-HEALING)
            extracted_json = extract_json_from_text(message.content or "")

            # Check if it extracted ANY valid JSON dictionary or list
            # Check if it extracted ANY valid JSON dictionary or list
            if extracted_json and extracted_json.strip().startswith(("{", "[")):
                try:
                    parsed_data = json.loads(extracted_json)

                    # ⚡ SELF-HEALING 1: The LLM hallucinated just the tool object
                    if (
                        isinstance(parsed_data, dict)
                        and "tool_name" in parsed_data
                        and "thought_process" not in parsed_data
                    ):
                        # Actively repair the mangled parameters
                        params = parsed_data.get("parameters", {})
                        if isinstance(params, str):
                            try:
                                params = json.loads(params)
                            except Exception:
                                params = {"raw_params": params}
                        if not isinstance(params, dict):
                            # If it flattened the arguments into the root, scoop them up
                            params = {
                                k: v
                                for k, v in parsed_data.items()
                                if k
                                not in ["tool_name", "reasoning", "thought_process"]
                            }

                        reasoning = parsed_data.get(
                            "reasoning", "Executing requested tool autonomously."
                        )

                        parsed_schema = AgentResponseSchema(
                            thought_process=reasoning,
                            tool_calls=[
                                ToolCallSchema(
                                    tool_name=parsed_data["tool_name"],
                                    parameters=params,
                                    reasoning=reasoning,
                                )
                            ],
                            final_response=None,
                        )

                    # ⚡ SELF-HEALING 2: The LLM hallucinated an array of tool objects
                    elif (
                        isinstance(parsed_data, list)
                        and len(parsed_data) > 0
                        and "tool_name" in parsed_data[0]
                    ):
                        healed_tools = []
                        for t in parsed_data:
                            params = t.get("parameters", {})
                            if isinstance(params, str):
                                try:
                                    params = json.loads(params)
                                except Exception:
                                    params = {"raw_params": params}
                            if not isinstance(params, dict):
                                params = {
                                    k: v
                                    for k, v in t.items()
                                    if k
                                    not in ["tool_name", "reasoning", "thought_process"]
                                }

                            healed_tools.append(
                                ToolCallSchema(
                                    tool_name=t["tool_name"],
                                    parameters=params,
                                    reasoning=t.get(
                                        "reasoning", "Executing tool autonomously."
                                    ),
                                )
                            )

                        parsed_schema = AgentResponseSchema(
                            thought_process="Executing multiple tools simultaneously.",
                            tool_calls=healed_tools,
                            final_response=None,
                        )

                    # PERFECT COMPLIANCE: The LLM followed the root schema perfectly
                    else:
                        parsed_schema = AgentResponseSchema.model_validate(parsed_data)

                    # 1. Translate pure JSON back into beautiful Markdown for Obsidian logs
                    human_readable_log = MarkdownTranslator.render_agent_log(
                        parsed_schema
                    )
                    final_text += human_readable_log + "\n"

                    # 2. Store the raw JSON in the context window
                    message_dict["content"] = extracted_json
                    messages.append(message_dict)

                    # 3. Synthesize the JSON tool schemas back into the format the Motor Cortex expects
                    if parsed_schema.tool_calls:

                        class MockFunction:
                            def __init__(self, name, arguments):
                                self.name = name
                                self.arguments = (
                                    json.dumps(arguments)
                                    if isinstance(arguments, dict)
                                    else arguments
                                )

                        class MockToolCall:
                            def __init__(self, id, function):
                                self.id = id
                                self.function = function

                        synthetic_tool_calls = [
                            MockToolCall(
                                id=f"call_{abs(hash(t.tool_name))}",
                                function=MockFunction(t.tool_name, t.parameters),
                            )
                            for t in parsed_schema.tool_calls
                        ]

                        # --- ⚡ DELEGATE TO MOTOR CORTEX ---
                        tool_messages, new_actions, halt_text = await execute_tools(
                            synthetic_tool_calls,
                            role_name,
                            step_index=iteration,
                            route=route,
                        )

                        # ⚡ ZERO-DEBT FIX: Flatten synthetic tool results into a standard user message
                        # so strict APIs (like Anthropic) don't crash expecting native tool_use_ids.
                        flat_results = "Tool Execution Results:\n"
                        for tm in tool_messages:
                            flat_results += f"{tm.get('content', '')}\n"

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
                    console.print(
                        f"[dim red]JSON Schema Parse/Heal Error: {e}[/dim red]"
                    )
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
            origin,  # ⚡ THE FIX: Pass the baton to the logger!
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
            origin,  # ⚡ THE FIX: Pass the baton to the logger!
        )
        return AgentResponse(text=error_msg, actions=action_manifest, usage=usage_data)
