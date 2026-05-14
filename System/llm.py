import asyncio
import json
import yaml  # type: ignore
import litellm  # type: ignore
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.neuroanatomy.limbic.hypothalamus import regulate_api_heartbeat
from System.neuroanatomy.systemic.immune_system import vault
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
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, default=str) + "\n")

        await asyncio.to_thread(_write)


def get_system_context(
    context_tags: list[str], domain: str = "NONE", prompt: str = ""
) -> str:
    context = ""
    memory_config_path = ROOT_DIR / "System" / "config" / "memory.yaml"

    try:
        with open(memory_config_path, "r", encoding="utf-8") as f:
            memory_map = yaml.safe_load(f).get("domains", {})
    except Exception:
        memory_map = {}

    for req in context_tags:
        target_folder = domain if req == "Domain" else req.upper()
        rel_path = memory_map.get(target_folder)

        if rel_path:
            path = ROOT_DIR / rel_path
            if path.exists():
                content = path.read_text(encoding="utf-8")

                if prompt:
                    from System.neuroanatomy.limbic.thalamus import filter_attention

                    content = filter_attention(prompt, content)

                context += f"\n\n--- {target_folder} MEMORY ---\n{content}\n------------------------------\n"

    return context


async def run_agent_async(
    role_name: str,
    model_string: str,
    system_prompt: str,
    user_prompt: str,
    tools: list[Any] | None = None,
    route: str = "UNKNOWN",
    domain: str = "NONE",
) -> AgentResponse:
    # ⚡ SHIFT-LEFT FIX: Declare variables outside the try block
    action_manifest: list[str] = []
    final_text: str = ""
    total_prompt: int = 0
    total_comp: int = 0

    try:
        from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere
        from System.neuroanatomy.cortical.motor_cortex import execute_tools

        model_string = route_hemisphere(route, model_string)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

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

            kwargs: dict[str, Any] = {
                "model": model_string,
                "messages": pruned_messages,
                "api_key": vault.get_api_key_for_model(model_string),
            }
            if tools:
                kwargs["tools"] = tools

            # ⚡ NATIVE ASYNC API CALL
            response = await regulate_api_heartbeat(acompletion, **kwargs)

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
        await log_interaction(
            role_name,
            model_string,
            system_prompt,
            user_prompt,
            final_text + "\n\nACTIONS:\n" + "\n".join(action_manifest),
            usage_data,
            route,
            domain,
        )
        return AgentResponse(
            text=final_text.strip(), actions=action_manifest, usage=usage_data
        )

    except Exception as e:
        error_msg = f"API/Execution Error: {str(e)}"
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
