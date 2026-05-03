import json
import re
import typer
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
)

load_dotenv()
app = typer.Typer(help="Brain OS: The Multi-Agent Life Operating System")
console = Console()

ORCHESTRATOR: str = "gemini/gemini-2.5-flash"
WORKER: str = "anthropic/claude-haiku-4-5"
AUDITOR: str = "openai/gpt-4o-mini"

LOG_DIR: Path = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE: Path = LOG_DIR / "agent_interactions.jsonl"


@dataclass
class AgentResponse:
    """Structured payload extraction to prevent token bloat."""

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
    domain: str = "NONE",  # <-- Added Domain Tracking
) -> None:
    """Logs full interactions for local observability and debugging."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "route": route,
        "domain": domain,  # <-- Added to log payload
        "agent": role_name,
        "model": model_string,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "response": response_content,
        "tokens": usage,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, default=str) + "\n")


def get_system_context(domain: str = "NONE") -> str:
    """Dynamically stacks Global Memory and Domain Memory to optimize token usage."""
    context = ""

    # 1. Always load Global Memory
    global_memory_path = Path(__file__).parent.parent / "Meta" / "global-memory.md"
    if global_memory_path.exists():
        memory_content = global_memory_path.read_text(encoding="utf-8")
        context += f"\n\n--- GLOBAL SYSTEM MEMORY ---\n{memory_content}\n----------------------------\n"

    # 2. Conditionally load Domain Memory
    if domain in ["PERSONAL", "PROFESSIONAL", "STUDIO"]:
        folder_name = domain.capitalize()
        file_name = f"{domain.lower()}-memory.md"
        domain_memory_path = Path(__file__).parent.parent / folder_name / file_name

        if domain_memory_path.exists():
            domain_content = domain_memory_path.read_text(encoding="utf-8")
            context += f"\n--- {domain} DOMAIN MEMORY ---\n{domain_content}\n------------------------------\n"

    return context


def run_agent(
    role_name: str,
    model_string: str,
    system_prompt: str,
    user_prompt: str,
    tools: list[Any] | None = None,
    route: str = "UNKNOWN",
    domain: str = "NONE",  # <-- Add domain parameter
) -> AgentResponse:
    try:
        # --- AUTO-INJECTOR: HIERARCHICAL CONTEXT ---
        system_context = get_system_context(domain)
        full_system_prompt = system_prompt + system_context

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        action_manifest: list[str] = []
        final_text: str = ""

        # MyPy fix: explicitly type these as integers
        total_prompt: int = 0
        total_comp: int = 0

        for step in range(5):
            # MyPy fix: explicitly type kwargs
            kwargs: dict[str, Any] = {
                "model": model_string,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools

            response = completion(**kwargs)
            message = response.choices[0].message

            if hasattr(response, "usage") and response.usage:
                total_prompt += int(getattr(response.usage, "prompt_tokens", 0))
                total_comp += int(getattr(response.usage, "completion_tokens", 0))

            # MyPy fix: explicitly type message_dict
            message_dict: dict[str, Any] = {"role": "assistant"}

            if message.content:
                message_dict["content"] = message.content
                final_text += str(message.content) + "\n"

            if hasattr(message, "tool_calls") and message.tool_calls:
                # Ruff fix: Break up the long line so it doesn't violate length rules
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
                    # MyPy fix: cast these to strings explicitly
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
        )  # <-- Passed the route

        return AgentResponse(text=final_text.strip(), actions=action_manifest)
    except Exception as e:
        return AgentResponse(text=f"Error: {str(e)}", actions=[])


def analyze_task(prompt: str) -> tuple[bool, str, str, str, dict[str, int]]:
    """
    Combines Pre-Flight Security, Dynamic Routing, and Intent-based Domain Mapping.
    Returns: (is_valid, message, route_type, domain, usage_data)
    """
    prompt_lower = prompt.lower()
    zero_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # --- STAGE 1: PRE-FLIGHT (Deterministic Bouncer) ---
    # We use regex word boundaries (\b) to prevent the "brainstorm" -> "rm" trap
    forbidden_actions = [r"\bdelete\b", r"\bremove\b", r"\berase\b", r"\brm\b"]
    for action in forbidden_actions:
        if re.search(action, prompt_lower):
            # Clean up the regex syntax for the user error message
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

    # --- STAGE 2: THE ROUTER & DOMAIN MAPPER (LLM Switchboard) ---
    system_prompt = (
        "You are the Brain OS Dispatcher. Your job is to validate, route, and assign domains to user tasks.\n"
        "The OS ONLY has tools to list, read, write, and rename files inside Personal/, Professional/, and Studio/.\n\n"
        "STEP 1 (Pre-Flight): If the task is impossible given these tools, reply EXACTLY with: 'REJECTED: <reason>'\n\n"
        "STEP 2 (Routing): Assign to ONE route:\n"
        "- ROUTE: FAST (Task requires no file system tools. e.g., 'What is my name?', 'Summarize this')\n"
        "- ROUTE: READ_ONLY (Task only requires listing or reading files.)\n"
        "- ROUTE: COMPLEX (Task requires writing, creating, or renaming files.)\n\n"
        "STEP 3 (Domain Context): Determine which area of the user's life this task belongs to:\n"
        "- DOMAIN: PERSONAL (Health, journals, family, personal life)\n"
        "- DOMAIN: PROFESSIONAL (Business, marketing, goals, career)\n"
        "- DOMAIN: STUDIO (Coding, open-core, technical architecture, software projects)\n"
        "- DOMAIN: NONE (General knowledge questions that do not touch the Vault)\n\n"
        "OUTPUT FORMAT (Must be exactly 2 lines if approved):\n"
        "ROUTE: <route>\n"
        "DOMAIN: <domain>"
    ) + get_system_context()

    try:
        response = completion(
            model=AUDITOR,
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

    # --- DISPATCHER (Pre-Flight + Routing) ---
    with console.status(
        "[bold yellow]🛡️ Dispatcher is analyzing the task...[/bold yellow]",
        spinner="dots",
    ):
        # FIX: We now unpack 5 variables, including 'domain'
        is_valid, reason, route_type, domain, dispatch_usage = analyze_task(description)

    if not is_valid:
        console.print(
            Panel(f"[bold red]Task Rejected:[/bold red] {reason}", border_style="red")
        )
        log_interaction(
            role_name="Dispatcher (Bouncer)",
            model_string=AUDITOR,
            system_prompt="Dispatcher Routing Logic + Global Memory",
            user_prompt=description,
            response_content=f"REJECTED: {reason}",
            usage=dispatch_usage,
            route="REJECTED",
            domain="NONE",  # <-- Added domain
        )
        return

    # FIX: Update the console print to show the Domain
    console.print(
        f"[dim]✅ Pre-Flight Passed. Assigned Route: [bold]{route_type}[/bold] | Domain Context: [bold cyan]{domain}[/bold cyan][/dim]\n"
    )

    # --- ROUTE 1: FAST (Zero-Tool Bypass) ---
    if route_type == "FAST":
        with console.status(
            "[bold magenta]Orchestrator (Gemini) is answering directly...[/bold magenta]",
            spinner="dots",
        ):
            response = run_agent(
                "Orchestrator (Gemini)",
                ORCHESTRATOR,
                "You are a fast, helpful Life OS assistant. Answer the user directly.",
                description,
                route=route_type,  # <-- Add this
            )
        console.print(
            Panel(
                Markdown(response.text),
                title="[bold magenta]FAST Response[/bold magenta]",
                border_style="magenta",
            )
        )
        console.print("\n[bold green]✅ Task Complete.[/bold green]\n")
        return

    # --- TOOL DEFINITIONS ---
    base_tools = [
        {
            "type": "function",
            "function": {
                "name": "read_safe_file",
                "description": "Reads the text content of a file.",
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
                "description": "Lists all files and folders in a directory.",
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
                "description": "Writes content to a file. Allowed zones: Personal/, Professional/, Studio/.",
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
                "description": "Renames a file.",
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
                "description": "Appends text to a file. Automatically injects before </working_memory> if present.",
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

    # --- ROUTE 2 & 3: READ_ONLY and COMPLEX ---
    if route_type == "READ_ONLY":
        agent_tools = base_tools
        worker_system = "You are a read-only system explorer. Use your tools to find information. You CANNOT write files."
    else:  # COMPLEX
        agent_tools = base_tools + write_tools
        worker_system = "You are a highly structured system engineer. Break this task down into a clear plan. Use your tools to read, explore, or write files as necessary."

    with console.status(
        "[bold cyan]Worker (Claude) is thinking...[/bold cyan]", spinner="dots"
    ):
        claude_draft = run_agent(
            "Worker (Claude)",
            WORKER,
            worker_system,
            description,
            tools=agent_tools,
            route=route_type,
        )  # <-- Add this

    display_draft = claude_draft.text
    if claude_draft.actions:
        display_draft += "\n\n**Actions Taken:**\n" + "\n".join(
            [f"- {a}" for a in claude_draft.actions]
        )

    console.print(
        Panel(
            Markdown(display_draft),
            title="[bold cyan]Worker (Claude)'s Draft & Actions[/bold cyan]",
            border_style="cyan",
        )
    )

    # --- PAYLOAD EXTRACTION ---
    orchestrator_system = "You are the central orchestrator of a Life OS. Review the worker's plan and the metadata of the files it touched. Summarize it into a final, polished executive summary."
    orchestrator_prompt = (
        f"Worker Thoughts:\n{claude_draft.text}\n\nActions Taken:\n"
        + ("\n".join(claude_draft.actions) if claude_draft.actions else "None.")
    )

    with console.status(
        "[bold magenta]Orchestrator (Gemini) is thinking...[/bold magenta]",
        spinner="dots",
    ):
        final_output = run_agent(
            "Orchestrator (Gemini)",
            ORCHESTRATOR,
            orchestrator_system,
            orchestrator_prompt,
            route=route_type,
        )  # <-- Add this

    console.print(
        Panel(
            Markdown(final_output.text),
            title="[bold magenta]Orchestrator (Gemini)'s Synthesis[/bold magenta]",
            border_style="magenta",
        )
    )
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


if __name__ == "__main__":
    app()
