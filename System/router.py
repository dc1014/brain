import json
import os
import re
import typer
import yaml  # type: ignore
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion  # type: ignore
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from typing import Any

from System.tools import (
    write_safe_file,
    read_safe_file,
    list_safe_directory,
    rename_safe_file,
    append_safe_file,
    bootstrap_project,  # <-- Added
    execute_command,  # <-- Added
    operate_forge,
    copy_safe_file,
)

load_dotenv()
app = typer.Typer(help="Brain OS: The Multi-Agent Life Operating System")
console = Console()

# --- SHIFT-LEFT: SECURE CONFIG LOADING ---
# yaml.safe_load() prevents arbitrary code execution vulnerabilities
CONFIG_PATH = Path(__file__).parent / "agents.yaml"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        AGENT_CONFIG = yaml.safe_load(f)
except Exception as e:
    console.print(f"[bold red]Fatal Error loading agents.yaml:[/bold red] {e}")
    exit(1)

LOG_DIR: Path = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE: Path = LOG_DIR / "agent_interactions.jsonl"


@dataclass
class AgentResponse:
    text: str
    actions: list[str] = field(default_factory=list)


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
    requested_contexts: list[str], current_domain: str = "NONE"
) -> str:
    """Dynamically loads specific canonical folders as defined in the YAML route."""
    context = ""
    root_dir = Path(__file__).parent.parent

    for req in requested_contexts:
        target_folder = current_domain if req == "Domain" else req.upper()
        if target_folder == "META":
            path = root_dir / "Meta" / "global-memory.md"
        elif target_folder in ["PERSONAL", "PROFESSIONAL", "STUDIO"]:
            path = (
                root_dir
                / target_folder.capitalize()
                / f"{target_folder.lower()}-memory.md"
            )
        else:
            continue

        if path.exists():
            context += f"\n\n--- {target_folder} MEMORY ---\n{path.read_text(encoding='utf-8')}\n------------------------------\n"

    return context


def run_agent(
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

        for step in range(5):
            kwargs: dict[str, Any] = {"model": model_string, "messages": messages}
            if tools:
                kwargs["tools"] = tools

            response = completion(**kwargs)

            # --- SHIFT-LEFT: SAFETY FILTER CATCH ---
            # If a provider (like Gemini) blocks the prompt due to safety filters,
            # it returns an empty choices array. We must catch this gracefully.
            if not getattr(response, "choices", None) or len(response.choices) == 0:
                return AgentResponse(
                    text="API SECURITY BLOCK: The LLM provider returned an empty response. This usually means its internal safety filters were triggered by words like 'execute', 'shell', or 'terminate'.",
                    actions=action_manifest,
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
                processed_tools = []
                for t in message.tool_calls:
                    if hasattr(t, "model_dump"):
                        processed_tools.append(t.model_dump())
                    else:
                        processed_tools.append(t)
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

                    if func_name == "write_safe_file":
                        result = write_safe_file(
                            args.get("filepath", ""), args.get("content", "")
                        )
                        action_manifest.append(f"[WRITE] {args.get('filepath')}")
                    elif func_name == "read_safe_file":
                        result = read_safe_file(args.get("filepath", ""))
                        action_manifest.append(f"[READ] {args.get('filepath')}")
                    elif func_name == "list_safe_directory":
                        result = list_safe_directory(args.get("directory_path", ""))
                        action_manifest.append(f"[LIST] {args.get('directory_path')}")
                    elif func_name == "rename_safe_file":
                        result = rename_safe_file(
                            args.get("old_filepath", ""), args.get("new_filepath", "")
                        )
                        action_manifest.append(
                            f"[RENAME] {args.get('old_filepath')} -> {args.get('new_filepath')}"
                        )
                    elif func_name == "append_safe_file":
                        result = append_safe_file(
                            args.get("filepath", ""), args.get("content", "")
                        )
                        action_manifest.append(f"[APPEND] {args.get('filepath')}")
                    # --- NEW TOOLS ---
                    elif func_name == "bootstrap_project":
                        url = args.get(
                            "template_url",
                            "https://github.com/mrdanielcasper/forge.git",
                        )
                        result = bootstrap_project(args.get("project_name", ""), url)
                        action_manifest.append(
                            f"[BOOTSTRAP] {args.get('project_name')}"
                        )
                    elif func_name == "execute_command":
                        result = execute_command(
                            args.get("command", ""), args.get("directory_path", "")
                        )
                        action_manifest.append(
                            f"[EXECUTE] {args.get('command')} in {args.get('directory_path')}"
                        )
                    elif func_name == "operate_forge":
                        result = operate_forge(
                            args.get("project_name", ""), args.get("instruction", "")
                        )
                        action_manifest.append(
                            f"[OPERATE_FORGE] {args.get('project_name')}"
                        )
                    elif func_name == "copy_safe_file":
                        result = copy_safe_file(
                            args.get("source_filepath", ""),
                            args.get("dest_filepath", ""),
                        )
                        action_manifest.append(
                            f"[COPY] {args.get('source_filepath')} -> {args.get('dest_filepath')}"
                        )
                    else:
                        result = f"ERROR: Unknown tool {func_name}"

                    console.print(f"[dim]🔍 Tool Executed: {func_name}[/dim]")
                    messages.append(
                        {
                            "role": "tool",
                            "name": func_name,
                            "tool_call_id": tool_id,
                            "content": str(result),
                        }
                    )
                continue
            else:
                break

        usage_data = {
            "prompt_tokens": total_prompt,
            "completion_tokens": total_comp,
            "total_tokens": total_prompt + total_comp,
        }
        audit_trail = final_text + "\n\nACTIONS:\n" + "\n".join(action_manifest)
        log_interaction(
            role_name,
            model_string,
            system_prompt,
            user_prompt,
            audit_trail,
            usage_data,
            route,
            domain,
        )

        return AgentResponse(text=final_text.strip(), actions=action_manifest)
    except Exception as e:
        return AgentResponse(text=f"Error: {str(e)}", actions=[])


def analyze_task(prompt: str) -> tuple[bool, str, str, str, dict[str, int]]:
    prompt_lower = prompt.lower()
    zero_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # PRE-FLIGHT (Deterministic Bouncer)
    forbidden_actions = [r"\bdelete\b", r"\bremove\b", r"\berase\b", r"\brm\b"]
    for action in forbidden_actions:
        if re.search(action, prompt_lower):
            clean_word = action.replace(r"\b", "")
            return (
                False,
                f"Hard Rule: No delete tool. You asked to '{clean_word}'.",
                "NONE",
                "NONE",
                zero_usage,
            )

    forbidden_targets = ["system/", ".env", "tools.py", "router.py"]
    for target in forbidden_targets:
        if target in prompt_lower:
            return (
                False,
                f"Hard Rule: Sandboxed. Cannot target '{target}'.",
                "NONE",
                "NONE",
                zero_usage,
            )

    # DYNAMIC DISPATCHER
    dispatcher_cfg = AGENT_CONFIG["agents"]["dispatcher"]
    system_prompt = dispatcher_cfg["system_prompt"] + get_system_context(["Meta"])

    try:
        response = completion(
            model=AGENT_CONFIG["models"][dispatcher_cfg["model"]],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        result = str(response.choices[0].message.content).strip().upper()

        usage_data = zero_usage.copy()
        if hasattr(response, "usage") and response.usage:
            usage_data["prompt_tokens"] = int(
                getattr(response.usage, "prompt_tokens", 0)
            )
            usage_data["completion_tokens"] = int(
                getattr(response.usage, "completion_tokens", 0)
            )
            usage_data["total_tokens"] = int(getattr(response.usage, "total_tokens", 0))

        if result.startswith("REJECTED:"):
            return (
                False,
                result.replace("REJECTED:", "").strip(),
                "NONE",
                "NONE",
                usage_data,
            )

        route = "COMPLEX"
        domain = "NONE"
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("ROUTE:"):
                route = line.split("ROUTE:")[1].strip()
            elif line.startswith("DOMAIN:"):
                domain = line.split("DOMAIN:")[1].strip()

        return True, "Approved.", route, domain, usage_data

    except Exception as e:
        return False, f"Dispatcher API Error: {str(e)}", "NONE", "NONE", zero_usage


@app.command()
def task(
    description: str = typer.Argument(..., help="The task you want the AI to perform."),
) -> None:
    console.print(
        f"\n[bold green]🚀 Initializing Life OS task:[/bold green] '{description}'\n"
    )

    with console.status(
        "[bold yellow]🛡️ Dispatcher is analyzing the task...[/bold yellow]",
        spinner="dots",
    ):
        is_valid, reason, route_type, domain, dispatch_usage = analyze_task(description)

    if not is_valid:
        console.print(
            Panel(f"[bold red]Task Rejected:[/bold red] {reason}", border_style="red")
        )
        log_interaction(
            "Dispatcher (Bouncer)",
            AGENT_CONFIG["models"]["gpt_mini"],
            "Dispatcher Logic",
            description,
            f"REJECTED: {reason}",
            dispatch_usage,
            "REJECTED",
            "NONE",
        )
        return

    console.print(
        f"[dim]✅ Pre-Flight Passed. Assigned Route: [bold]{route_type}[/bold] | Domain Context: [bold cyan]{domain}[/bold cyan][/dim]\n"
    )

    # --- TOOL DEFINITIONS ---
    base_tools = [
        {
            "type": "function",
            "function": {
                "name": "read_safe_file",
                "description": "Reads file text.",
                "parameters": {
                    "type": "object",
                    "properties": {"filepath": {"type": "string"}},
                    "required": ["filepath"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_safe_directory",
                "description": "Lists files/folders.",
                "parameters": {
                    "type": "object",
                    "properties": {"directory_path": {"type": "string"}},
                    "required": ["directory_path"],
                },
            },
        },
    ]
    write_tools = [
        {
            "type": "function",
            "function": {
                "name": "write_safe_file",
                "description": "Writes file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["filepath", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "rename_safe_file",
                "description": "Renames file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "old_filepath": {"type": "string"},
                        "new_filepath": {"type": "string"},
                    },
                    "required": ["old_filepath", "new_filepath"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "append_safe_file",
                "description": "Appends to file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["filepath", "content"],
                },
            },
        },
    ]
    execute_tools = [
        {
            "type": "function",
            "function": {
                "name": "bootstrap_project",
                "description": "Clones a project archetype into Studio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "template_url": {
                            "type": "string",
                            "description": "Optional Git URL, defaults to Forge",
                        },
                    },
                    "required": ["project_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "Runs a terminal command. DO NOT EXPECT OUTPUT in the response. Check the file system after it runs to see side effects.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "directory_path": {"type": "string"},
                    },
                    "required": ["command", "directory_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "operate_forge",
                "description": "Operates a Forge archetype project securely. Use this INSTEAD of execute_command to run Forge. Automatically handles handoff.md and retrieves telemetry.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "The exact name of the project folder in Studio/ (e.g., 'Brain-Website').",
                        },
                        "instruction": {
                            "type": "string",
                            "description": "The natural language instruction or pipeline command (e.g., '[START: Engineering] Build the React site').",
                        },
                    },
                    "required": ["project_name", "instruction"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "copy_safe_file",
                "description": "Copies a file. Useful for moving images from Media/ into Studio/ projects.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source_filepath": {"type": "string"},
                        "dest_filepath": {"type": "string"},
                    },
                    "required": ["source_filepath", "dest_filepath"],
                },
            },
        },
    ]
    available_tools = {
        "base": base_tools,
        "write": write_tools,
        "execute": execute_tools,
    }

    # --- EXECUTE DECLARATIVE PIPELINE ---
    pipeline = AGENT_CONFIG["routes"].get(route_type, [])
    current_payload = description

    for step in pipeline:
        # SHIFT-LEFT: Dynamic queue allows the Auditor to autonomously reject and retry
        pipeline = list(AGENT_CONFIG["routes"].get(route_type, []))
        current_payload = description
        eval_retries = 0
        MAX_RETRIES = 2

        while len(pipeline) > 0:
            step = pipeline.pop(0)
            agent_cfg = AGENT_CONFIG["agents"][step["agent"]]

            # --- ZERO-CONFIG MODEL FALLBACK ---
            desired_model_key = agent_cfg["model"]
            env_key_map = {
                "gpt_mini": "OPENAI_API_KEY",
                "claude_haiku": "ANTHROPIC_API_KEY",
                "gemini_flash": "GEMINI_API_KEY",
                "claude_sonnet": "ANTHROPIC_API_KEY",  # <-- ADD THIS LINE!
            }

            if os.getenv(env_key_map.get(desired_model_key, "")):
                model_str = AGENT_CONFIG["models"][desired_model_key]
            else:
                if os.getenv("OPENAI_API_KEY"):
                    model_str = AGENT_CONFIG["models"]["gpt_mini"]
                elif os.getenv("ANTHROPIC_API_KEY"):
                    model_str = AGENT_CONFIG["models"]["claude_haiku"]
                elif os.getenv("GEMINI_API_KEY"):
                    model_str = AGENT_CONFIG["models"]["gemini_flash"]
                else:
                    model_str = AGENT_CONFIG["models"][desired_model_key]

            # Build Tools and Context dynamically
            active_tools = []
            for t_group in step.get("tools", []):
                active_tools.extend(available_tools.get(t_group, []))

            full_system_prompt = agent_cfg["system_prompt"] + get_system_context(
                step.get("context", []), domain
            )

            console.print(
                f"\n[bold cyan]⏳ {agent_cfg['name']} is working...[/bold cyan]"
            )

            step_result = run_agent(
                role_name=agent_cfg["name"],
                model_string=model_str,
                system_prompt=full_system_prompt,
                user_prompt=current_payload,
                tools=active_tools if active_tools else None,
                route=route_type,
                domain=domain,
            )

            # Print Output
            display_text = step_result.text
            if step_result.actions:
                display_text += "\n\n**Actions Taken:**\n" + "\n".join(
                    [f"- {a}" for a in step_result.actions]
                )

            console.print(
                Panel(
                    Markdown(display_text),
                    title=f"[bold cyan]{agent_cfg['name']}[/bold cyan]",
                    border_style="cyan",
                )
            )

            # --- LAYER 2 EVALUATION LOOP ---
            if step["agent"] == "auditor" and "[GRADE: FAIL]" in step_result.text:
                if eval_retries < MAX_RETRIES:
                    console.print(
                        "\n[bold red]❌ Audit Failed! Routing back to Engineer for autonomous fix...[/bold red]\n"
                    )
                    # Re-queue the Engineer and Auditor
                    pipeline.insert(
                        0,
                        {
                            "agent": "auditor",
                            "tools": ["base"],
                            "context": ["Meta", "Domain", "Studio"],
                        },
                    )
                    pipeline.insert(
                        0,
                        {
                            "agent": "engineer",
                            "tools": ["base", "write", "execute"],
                            "context": ["Meta", "Domain", "Studio"],
                        },
                    )

                    # SHIFT-LEFT: Preserve the original task context so the Engineer doesn't get lost
                    current_payload = f"Original Task: {description}\n\nCRITICAL - AUDIT FAILED. Read the critique, fix the code, and redeploy:\n\n{step_result.text}"
                    eval_retries += 1
                    continue
                else:
                    console.print(
                        "\n[bold red]🛑 CIRCUIT BREAKER: Max eval retries reached. Halting pipeline.[/bold red]\n"
                    )
                    break

            # Hand-off Pipeline Payload (Normal flow)
            current_payload = f"Original Task: {description}\n\nPrevious Agent ({agent_cfg['name']}) Output:\n{step_result.text}\n\nActions Taken:\n{step_result.actions}"

        console.print("\n[bold green]✅ Task Complete.[/bold green]\n")


@app.command()
def logs(
    limit: int = typer.Option(3, help="Number of recent interactions to display."),
) -> None:
    if not LOG_FILE.exists():
        console.print("[bold red]No logs found. Run a task first![/bold red]")
        return
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    recent_lines = lines[-limit:]
    console.print(
        f"\n[bold green]📊 Showing last {len(recent_lines)} interactions:[/bold green]\n"
    )
    for line in recent_lines:
        data = json.loads(line)
        meta_text = f"[bold cyan]Agent:[/bold cyan] {data['agent']}\n[bold cyan]Model:[/bold cyan] {data['model']}\n[bold cyan]Time:[/bold cyan] {data['timestamp']}\n[bold cyan]Tokens:[/bold cyan] {data.get('tokens', {})}"
        console.print(
            Panel(meta_text, title="Interaction Metadata", border_style="cyan")
        )
        console.print(
            Panel(Markdown(data["response"]), title="AI Response", border_style="white")
        )
        console.print("\n" + "=" * 50 + "\n")


@app.command()
def sleep(
    synaptic: bool = typer.Option(
        False,
        "--synaptic",
        help="Use experimental GPU weight-training instead of Markdown files.",
    ),
) -> None:
    console.print("\n[bold blue]🌙 Initiating Sleep Cycle...[/bold blue]")
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        console.print("[dim]No daily logs found. Brain OS is already rested.[/dim]\n")
        return

    with console.status(
        "[bold cyan]Reading daily interactions...[/bold cyan]", spinner="dots"
    ):
        logs_content = LOG_FILE.read_text(encoding="utf-8")
        log_lines = logs_content.strip().split("\n")
    console.print(f"[dim]Found {len(log_lines)} interactions to consolidate.[/dim]")

    system_prompt = (
        "You are the Brain OS Sleep Compactor. Extract PERMANENT, VALUABLE facts from these logs.\n"
        'EXPECTED JSON FORMAT:\n{\n  "META": ["Fact 1"],\n  "PERSONAL": ["Fact 2"],\n  "PROFESSIONAL": ["Fact 3"],\n  "STUDIO": ["Fact 4"]\n}'
    )

    with console.status(
        "[bold magenta]Compacting short-term memory...[/bold magenta]", spinner="dots"
    ):
        try:
            # We hardcode the Auditor here as it guarantees JSON output
            response = completion(
                model=AGENT_CONFIG["models"]["gpt_mini"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": logs_content},
                ],
                response_format={"type": "json_object"},
            )
            memories = json.loads(str(response.choices[0].message.content).strip())
        except Exception as e:
            console.print(
                f"[bold red]Sleep Cycle Interrupted (API/JSON Error):[/bold red] {str(e)}"
            )
            return

    domains = {
        "META": "Meta/global-memory.md",
        "PERSONAL": "Personal/personal-memory.md",
        "PROFESSIONAL": "Professional/professional-memory.md",
        "STUDIO": "Studio/studio-memory.md",
    }
    memories_saved = 0

    with console.status(
        "[bold yellow]Injecting synapses into Vault...[/bold yellow]", spinner="dots"
    ):
        for domain, facts in memories.items():
            if facts and isinstance(facts, list):
                filepath = domains.get(domain.upper())
                if filepath:
                    bullet_facts = "\n".join([f"- {fact}" for fact in facts])
                    result = append_safe_file(filepath, bullet_facts)
                    if "SUCCESS" in result:
                        memories_saved += len(facts)
                        console.print(
                            f"[green]✓ Appended {len(facts)} facts into {domain} markdown.[/green]"
                        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    LOG_FILE.rename(LOG_DIR / f"archive_{timestamp}.jsonl")
    console.print(
        f"\n[bold green]🌅 Sleep Cycle Complete.[/bold green] [dim]Consolidated {memories_saved} new core memories.[/dim]\n"
    )


@app.command()
def init() -> None:
    """Automated zero-friction onboarding: Builds the Vault and foundational memory files."""
    console.print("\n[bold blue]🚀 Initializing Brain OS Vault...[/bold blue]")
    root_dir = Path(__file__).parent.parent

    # SHIFT-LEFT: Added "Media" to the automated creation list
    for dir_name in ["Personal", "Professional", "Studio", "Meta", "Media", "logs"]:
        dir_path = root_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✓ Created directory:[/green] {dir_name}/")
        else:
            console.print(f"[dim]✓ Directory exists:[/dim] {dir_name}/")

    memories = {
        "Meta/global-memory.md": "# Brain OS: Global Memory\n\n<user_persona>\n- Name: User\n</user_persona>\n\n<working_memory>\n- Brain OS successfully initialized.\n</working_memory>\n",
        "Personal/personal-memory.md": "# Personal Memory\n\n<working_memory>\n</working_memory>\n",
        "Professional/professional-memory.md": "# Professional Memory\n\n<working_memory>\n</working_memory>\n",
        "Studio/studio-memory.md": "# Studio Memory\n\n<working_memory>\n</working_memory>\n",
    }
    for file_path, content in memories.items():
        full_path = root_dir / file_path
        if not full_path.exists():
            full_path.write_text(content, encoding="utf-8")
            console.print(f"[green]✓ Created file:[/green] {file_path}")
        else:
            console.print(f"[dim]✓ File exists:[/dim] {file_path}")

    env_example, env_file = root_dir / ".env.example", root_dir / ".env"
    if env_example.exists() and not env_file.exists():
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
        console.print("[green]✓ Created file:[/green] .env (Copied from template)")

    console.print("\n[bold green]✅ Initialization Complete![/bold green]\n")


if __name__ == "__main__":
    app()
