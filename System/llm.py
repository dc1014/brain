import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml  # type: ignore

from litellm import acompletion  # type: ignore
from rich.console import Console

from System.tools import (
    write_safe_file,
    read_safe_file,
    list_safe_directory,
    rename_safe_file,
    append_safe_file,
    bootstrap_project,
    execute_command,
    operate_forge,
    copy_safe_file,
    search_safe_directory,
)

console = Console()

LOG_DIR: Path = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE: Path = LOG_DIR / "agent_interactions.jsonl"


@dataclass
class AgentResponse:
    text: str
    actions: list[str] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)


def log_interaction(
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
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, default=str) + "\n")


def get_system_context(
    context_tags: list[str], domain: str = "NONE", prompt: str = ""
) -> str:
    """Dynamically loads specific canonical folders and passes them through the Thalamus."""
    context = ""
    root_dir = Path(__file__).parent.parent
    memory_config_path = Path(__file__).parent / "config" / "memory.yaml"

    try:
        with open(memory_config_path, "r", encoding="utf-8") as f:
            memory_map = yaml.safe_load(f).get("domains", {})
    except Exception:
        memory_map = {}

    for req in context_tags:
        target_folder = domain if req == "Domain" else req.upper()
        rel_path = memory_map.get(target_folder)

        if rel_path:
            path = root_dir / rel_path
            if path.exists():
                content = path.read_text(encoding="utf-8")

                # --- 🧠 THALAMUS TRIGGER (Semantic Attention) ---
                if prompt:
                    from System.organs.thalamus import filter_attention

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
    try:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        action_manifest: list[str] = []
        final_text: str = ""
        total_prompt: int = 0
        total_comp: int = 0

        for step in range(15):
            if len(messages) > 7:
                window = messages[-5:]
                while window and window[0].get("role") == "tool":
                    window.pop(0)
                pruned_messages = [messages[0], messages[1]] + window
            else:
                pruned_messages = messages

            import os

            _has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
            _has_openai = bool(os.environ.get("OPENAI_API_KEY"))

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
            }
            if tools:
                kwargs["tools"] = tools

            # ⚡ NATIVE ASYNC API CALL ⚡
            response = await acompletion(**kwargs)

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

            if hasattr(message, "tool_calls") and message.tool_calls:
                if step == 0:
                    console.print(
                        f"\n[dim]⚡ {role_name} is thinking and acting...[/dim]"
                    )

                for tool_call in message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    func_name = str(tool_call.function.name)
                    tool_id = str(tool_call.id)

                    # ⚡ OFF-LOAD SYNC TOOLS TO THREADS ⚡
                    if func_name == "write_safe_file":
                        result = await asyncio.to_thread(
                            write_safe_file,
                            args.get("filepath", ""),
                            args.get("content", ""),
                        )
                        action_manifest.append(f"[WRITE] {args.get('filepath')}")
                    elif func_name == "search_safe_directory":
                        result = await asyncio.to_thread(
                            search_safe_directory,
                            args.get("query", ""),
                            args.get("directory_path", ""),
                        )
                        action_manifest.append(
                            f"[SEARCH] '{args.get('query')}' in {args.get('directory_path')}"
                        )
                    elif func_name == "read_safe_file":
                        result = await asyncio.to_thread(
                            read_safe_file, args.get("filepath", "")
                        )
                        action_manifest.append(f"[READ] {args.get('filepath')}")
                    elif func_name == "list_safe_directory":
                        result = await asyncio.to_thread(
                            list_safe_directory, args.get("directory_path", "")
                        )
                        action_manifest.append(f"[LIST] {args.get('directory_path')}")
                    elif func_name == "rename_safe_file":
                        result = await asyncio.to_thread(
                            rename_safe_file,
                            args.get("old_filepath", ""),
                            args.get("new_filepath", ""),
                        )
                        action_manifest.append(
                            f"[RENAME] {args.get('old_filepath')} -> {args.get('new_filepath')}"
                        )
                    elif func_name == "append_safe_file":
                        result = await asyncio.to_thread(
                            append_safe_file,
                            args.get("filepath", ""),
                            args.get("content", ""),
                        )
                        action_manifest.append(f"[APPEND] {args.get('filepath')}")
                    elif func_name == "bootstrap_project":
                        url = args.get(
                            "template_url",
                            "https://github.com/mrdanielcasper/forge.git",
                        )
                        result = await asyncio.to_thread(
                            bootstrap_project, args.get("project_name", ""), url
                        )
                        action_manifest.append(
                            f"[BOOTSTRAP] {args.get('project_name')}"
                        )
                    elif func_name == "execute_command":
                        result = await asyncio.to_thread(
                            execute_command,
                            args.get("command", ""),
                            args.get("directory_path", ""),
                        )
                        action_manifest.append(
                            f"[EXECUTE] {args.get('command')} in {args.get('directory_path')}"
                        )
                    elif func_name == "operate_forge":
                        result = await asyncio.to_thread(
                            operate_forge,
                            args.get("project_name", ""),
                            args.get("instruction", ""),
                        )
                        action_manifest.append(
                            f"[OPERATE_FORGE] {args.get('project_name')}"
                        )
                    elif func_name == "copy_safe_file":
                        result = await asyncio.to_thread(
                            copy_safe_file,
                            args.get("source_filepath", ""),
                            args.get("dest_filepath", ""),
                        )
                        action_manifest.append(
                            f"[COPY] {args.get('source_filepath')} -> {args.get('dest_filepath')}"
                        )
                    elif func_name == "speak":
                        from System.tools import speak

                        result = await asyncio.to_thread(speak, args.get("text", ""))
                        action_manifest.append(
                            f"[SPEAK] {args.get('text', '')[:20]}..."
                        )
                    elif func_name == "analyze_audio":
                        from System.tools import analyze_audio

                        result = await asyncio.to_thread(
                            analyze_audio, args.get("filepath", "")
                        )
                        action_manifest.append(
                            f"[ANALYZE_AUDIO] {args.get('filepath', '')}"
                        )
                    else:
                        result = f"ERROR: Unknown tool {func_name}"

                    console.print(f"[dim]🔍 Tool Executed: {func_name}[/dim]")

                    raw_output = str(result)
                    MAX_CHARS = 8000
                    truncated_output = raw_output[:MAX_CHARS] + (
                        f"\n\n... [SYSTEM WARNING: Truncated at {MAX_CHARS} chars]"
                        if len(raw_output) > MAX_CHARS
                        else ""
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "name": func_name,
                            "tool_call_id": tool_id,
                            "content": truncated_output,
                        }
                    )

                    if str(result).startswith("SECURITY BLOCK") or str(
                        result
                    ).startswith("<shell_output>\n<stderr>\nSECURITY BLOCK"):
                        final_text += f"\n\n[SYSTEM HALT] {result}"
                        action_manifest.append("[HALTED] Security clearance denied.")
                        return AgentResponse(
                            text=final_text.strip(),
                            actions=action_manifest,
                            usage={
                                "prompt_tokens": total_prompt,
                                "completion_tokens": total_comp,
                                "total_tokens": total_prompt + total_comp,
                            },
                        )
                continue
            else:
                break

        usage_data = {
            "prompt_tokens": total_prompt,
            "completion_tokens": total_comp,
            "total_tokens": total_prompt + total_comp,
        }
        log_interaction(
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
        log_interaction(
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
