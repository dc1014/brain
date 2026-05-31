# --- System/llm.py ---
from System.core.schemas import AgentResponseSchema, MarkdownTranslator
import asyncio
import json
import litellm  # type: ignore
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.neuroanatomy.systemic.immune_system import vault
from System.neuroanatomy.systemic.endocrine import EndocrineSystem
from System.neuroanatomy.autonomic.interoception import get_current_metabolism

from litellm import acompletion  # type: ignore

litellm.telemetry = False
litellm.drop_params = True

console = Console()

LOG_DIR: Path = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE: Path = LOG_DIR / "agent_interactions.jsonl"


def clean_json_output(text: str) -> str:
    if not text:
        return "{}"

    # Strip common markdown blocks
    text = text.strip("`").removeprefix("json").strip()

    # Find the first occurrence of '{' or '['
    start_brace = text.find("{")
    start_bracket = text.find("[")

    start_idx = -1
    if start_brace != -1 and start_bracket != -1:
        start_idx = min(start_brace, start_bracket)
    elif start_brace != -1:
        start_idx = start_brace
    elif start_bracket != -1:
        start_idx = start_bracket

    # Find the corresponding end bracket and slice the string
    if start_idx != -1:
        end_idx = text.rfind("}") if text[start_idx] == "{" else text.rfind("]")
        if end_idx != -1 and end_idx > start_idx:
            return text[start_idx : end_idx + 1]

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
    origin: str = "HUMAN",
    goal_thread: str | None = None,
) -> None:
    # Mask secrets BEFORE constructing the log entry object
    safe_response_content = vault.mask_secrets(response_content)
    safe_user_prompt = vault.mask_secrets(user_prompt)

    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent": role_name,
        "route": route,
        "domain": domain,
        "origin": origin,
        "goal_thread": goal_thread,  # ⚡ Safely mapped
        "user_prompt": safe_user_prompt,
        "response": safe_response_content,
    }

    from System.neuroanatomy.cortical.motor_cortex import MotorCortex

    async with MotorCortex.get_lock(LOG_FILE):

        def _write():
            raw_json = json.dumps(log_entry, default=str)
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(raw_json + "\n")

        await asyncio.to_thread(_write)


def get_system_context(
    role_name: str | list[str], system_prompt: str = "", prompt: str = "", **kwargs
) -> str:
    from System.core.dna import get_dna_config

    roles = role_name if isinstance(role_name, list) else [role_name]
    base_prompt = system_prompt + "\n" if system_prompt else ""

    for r in roles:
        agent_data = get_dna_config().get("agents", {}).get(r.lower(), {})
        base_prompt += (
            agent_data.get("system_prompt", f"You are the {r} node of CoreTex OS.")
            + "\n"
        )

    if prompt:
        base_prompt += f"\n{prompt}\n"

    try:
        from System.neuroanatomy.limbic.nucleus_accumbens import get_plasticity_rules

        plasticity = get_plasticity_rules()
        if plasticity:
            base_prompt += (
                f"\n\nCRITICAL LEARNED BEHAVIORS (From Past Failures):\n{plasticity}\n"
            )
    except ImportError:
        pass

    code_execution_enabled = os.environ.get(
        "CORETEX_ENABLE_CODE_EXECUTION", "false"
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
    endocrine = EndocrineSystem()
    vector = endocrine.get_humoral_vector()

    temp = 0.5 + (vector["dopamine"] * 0.4) - (vector["cortisol"] * 0.4)
    final_temp = max(0.0, min(1.0, temp))

    final_model = base_model
    if vector["cortisol"] > 0.7:
        from System.core.dna import get_dna_config

        fast_model = get_dna_config().get("models", {}).get("fast", base_model)
        if fast_model != base_model:
            final_model = fast_model
            console.print(
                "[dim magenta]Cortisol Overload: Routing to efficiency matrix.[/dim magenta]"
            )

    max_tokens = endocrine.calculate_token_limit(final_model)

    return final_model, final_temp, max_tokens


async def run_agent_async(
    role_name: str,
    system_prompt: str,
    user_prompt: str,
    model_string: str,
    tools: list | None = None,
    route: str = "WORKSPACE",
    domain: str = "GENERAL",
    origin: str = "HUMAN",
    goal_thread: str | None = None,
):

    metabolism_data = get_current_metabolism()
    is_exhausted = metabolism_data.get("exhausted", False)
    if is_exhausted:
        return AgentResponse(
            text="API SECURITY BLOCK: Daily token budget exhausted. System is in refractory sleep state.",
            actions=[],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    mod_model, mod_temp, mod_tokens = apply_humoral_modulation(model_string)

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
    total_comp = 0
    final_text = ""
    action_manifest: list[str] = []

    try:
        from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere
        from System.neuroanatomy.cortical.motor_cortex import execute_tools
        from System.neuroanatomy.cortical.working_memory import compress_message_array

        model_string = route_hemisphere(route, model_string)
        current_target_model = mod_model

        for iteration in range(5):
            messages = await compress_message_array(messages, model_string)
            pruned_messages = messages

            routed_model, api_key = vault.resolve_routing(current_target_model)

            gateway_url = vault.get_secret("GATEWAY_BASE_URL")
            if gateway_url:
                api_key = vault.get_secret("GATEWAY_API_KEY") or api_key

            completion_kwargs: Dict[str, Any] = {
                "model": routed_model,
                "messages": pruned_messages,
                "tools": tools,
                "temperature": mod_temp,
                "max_tokens": mod_tokens,
                "api_key": api_key,
            }

            if gateway_url:
                completion_kwargs["api_base"] = gateway_url

            if not tools:
                completion_kwargs["response_format"] = AgentResponseSchema

            response = await acompletion(**completion_kwargs)

            if not getattr(response, "choices", None) or len(response.choices) == 0:
                return AgentResponse(
                    text="API SECURITY BLOCK: Empty response.", actions=action_manifest
                )

            message = response.choices[0].message

            if hasattr(response, "usage") and response.usage:
                total_prompt += int(getattr(response.usage, "prompt_tokens", 0))
                total_comp += int(getattr(response.usage, "completion_tokens", 0))

            message_dict: dict[str, Any] = {"role": "assistant"}
            clean_json = clean_json_output(message.content or "")

            if clean_json and clean_json.startswith(("{", "[")):
                try:
                    parsed_schema = AgentResponseSchema.model_validate_json(clean_json)

                    human_readable_log = MarkdownTranslator.render_agent_log(
                        parsed_schema
                    )
                    final_text += human_readable_log + "\n"

                    message_dict["content"] = clean_json
                    messages.append(message_dict)

                    if parsed_schema.tool_calls:
                        tool_messages, new_actions, halt_text = await execute_tools(
                            parsed_schema.tool_calls,
                            role_name,
                            step_index=iteration,
                            route=route,
                        )

                        flat_results = "Tool Execution Results:\n"
                        for tm in tool_messages:
                            content_str = tm.get("content", "")
                            if len(content_str) > 15000:
                                content_str = (
                                    content_str[:15000]
                                    + "\n\n... [ TRUNCATED: OUTPUT EXCEEDED 15,000 CHARACTERS. USE `grep`, `head`, OR `tail` ]"
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
            else:
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

                    for tm in tool_messages:
                        if (
                            isinstance(tm.get("content"), str)
                            and len(tm["content"]) > 15000
                        ):
                            tm["content"] = (
                                tm["content"][:15000]
                                + "\n\n... [ TRUNCATED: OUTPUT EXCEEDED 15,000 CHARACTERS. USE `grep`, `head`, OR `tail` ]"
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

        safe_final_text = vault.mask_secrets(final_text.strip())
        safe_action_manifest = [vault.mask_secrets(a) for a in action_manifest]

        log_content = safe_final_text
        if safe_action_manifest:
            log_content += "\n\nACTIONS:\n" + "\n".join(safe_action_manifest)

        await log_interaction(
            role_name,
            model_string,
            system_prompt,
            user_prompt,
            log_content,
            usage_data,
            route,
            domain,
            origin,
            goal_thread=goal_thread,
        )
        return AgentResponse(
            text=safe_final_text, actions=safe_action_manifest, usage=usage_data
        )

    except Exception as e:
        raw_error = str(e).lower()
        hint = ""

        # Catch common API key / Authentication issues
        if (
            "authentication" in raw_error
            or "api key" in raw_error
            or "unauthorized" in raw_error
            or "401" in raw_error
        ):
            hint = (
                "\n\n💡 **[Configuration Hint]**: Your LLM API key was rejected or missing. "
                "Check your `.env` file. If you are not using OpenRouter (the default), ensure you have provided the correct standard keys (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY) and that they are active."
            )
        # Catch downtime / routing failures
        elif "connection" in raw_error or "timeout" in raw_error or "502" in raw_error:
            hint = (
                "\n\n💡 **[Network Hint]**: The upstream LLM provider might be down or unreachable. "
                "If you enabled `USE_LOCAL_SLM=true`, ensure your local Ollama engine is actually running."
            )

        safe_error_msg = vault.mask_secrets(f"API/Execution Error: {str(e)}{hint}")

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
            safe_error_msg,
            usage_data,
            route,
            domain,
            origin,
            goal_thread=goal_thread,
        )
        return AgentResponse(
            text=safe_error_msg, actions=action_manifest, usage=usage_data
        )


async def compress_memory_buffer(current_text: str) -> str | None:
    safe_current_text = vault.mask_secrets(current_text)
    prompt = (
        "You are the Prefrontal Cortex. Synthesize the following pipeline activity into a highly "
        "concise, bulleted list of 'Established Facts' and 'Current State' wrapped in <summary_update> tags.\n"
        "Discard all conversational filler and preserve ONLY technical facts, code paths, and outcomes.\n\n"
        f"ACTIVITY LOG:\n{safe_current_text}"
    )
    try:
        from System.core.dna import get_dna_config

        model = (
            get_dna_config().get("models", {}).get("fast", "gemini/gemini-2.5-flash")
        )
        routed_model, api_key = vault.resolve_routing(model)

        gateway_url = vault.get_secret("GATEWAY_BASE_URL")
        if gateway_url:
            api_key = vault.get_secret("GATEWAY_API_KEY") or api_key

        kwargs = {
            "model": routed_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "api_key": api_key,
        }
        if gateway_url:
            kwargs["api_base"] = gateway_url

        response = await acompletion(**kwargs)
        return response.choices[0].message.content.strip()
    except Exception as e:
        console.print(f"[dim red]PFC Compression Failed: {e}[/dim red]")
        return None
