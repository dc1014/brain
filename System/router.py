import json
import typer
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion  # type: ignore
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from System.tools import write_safe_file, read_safe_file, list_safe_directory

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
    usage: dict,
) -> None:
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": role_name,
        "model": model_string,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "response": response_content,
        "tokens": usage,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, default=str) + "\n")


def run_agent(
    role_name: str,
    model_string: str,
    system_prompt: str,
    user_prompt: str,
    tools: list | None = None,
) -> AgentResponse:
    try:
        kwargs = {
            "model": model_string,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if tools:
            kwargs["tools"] = tools

        response = completion(**kwargs)
        message = response.choices[0].message
        content: str = str(message.content or "")
        action_manifest: list[str] = []

        # --- ISOLATED TOOL EXECUTION ---
        if hasattr(message, "tool_calls") and message.tool_calls:
            console.print(f"\n[dim]⚡ {role_name} is using tools...[/dim]")
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                func_name = tool_call.function.name

                if func_name == "write_safe_file":
                    result = write_safe_file(
                        args.get("filepath", ""), args.get("content", "")
                    )
                    # Only record the metadata, not the file contents
                    action_manifest.append(
                        f"[WRITE] {args.get('filepath')} - {result[:30]}..."
                    )
                elif func_name == "read_safe_file":
                    result = read_safe_file(args.get("filepath", ""))
                    action_manifest.append(
                        f"[READ] {args.get('filepath')} - Extracted {len(result)} chars."
                    )
                elif func_name == "list_safe_directory":
                    result = list_safe_directory(args.get("directory_path", ""))
                    action_manifest.append(
                        f"[LIST] {args.get('directory_path')} - Found {len(result.splitlines())} items."
                    )
                else:
                    action_manifest.append(f"[ERROR] Unknown tool {func_name}")

                console.print(f"[dim]🔍 Tool Executed: {func_name}[/dim]")

        usage_data: dict = {}
        if hasattr(response, "usage") and response.usage:
            usage_data = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }

        # Log the full audit trail for the JSONL file, but return the extracted payload
        audit_trail = content + "\n\nACTIONS:\n" + "\n".join(action_manifest)
        log_interaction(
            role_name, model_string, system_prompt, user_prompt, audit_trail, usage_data
        )

        return AgentResponse(text=content, actions=action_manifest)
    except Exception as e:
        return AgentResponse(text=f"Error: {str(e)}", actions=[])


@app.command()
def task(
    description: str = typer.Argument(..., help="The task you want the AI to perform."),
) -> None:
    console.print(
        f"\n[bold green]🚀 Initializing Life OS task:[/bold green] '{description}'\n"
    )

    agent_tools = [
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

    worker_system: str = "You are a highly structured system engineer. Break this task down into a clear plan. Use your tools to read, explore, or write files as necessary."

    with console.status(
        "[bold cyan]Worker (Claude) is thinking...[/bold cyan]", spinner="dots"
    ):
        claude_draft: AgentResponse = run_agent(
            "Worker (Claude)", WORKER, worker_system, description, tools=agent_tools
        )

    # Format what is shown in the terminal
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
    # We strictly limit what Gemini sees to save thousands of tokens
    orchestrator_system: str = "You are the central orchestrator of a Life OS. Review the worker's plan and the metadata of the files it touched. Summarize it into a final, polished executive summary."

    orchestrator_prompt: str = (
        f"Worker Thoughts:\n{claude_draft.text}\n\nActions Taken (Metadata Only):\n"
    )
    orchestrator_prompt += (
        "\n".join(claude_draft.actions) if claude_draft.actions else "None."
    )

    with console.status(
        "[bold magenta]Orchestrator (Gemini) is thinking...[/bold magenta]",
        spinner="dots",
    ):
        final_output: AgentResponse = run_agent(
            "Orchestrator (Gemini)",
            ORCHESTRATOR,
            orchestrator_system,
            orchestrator_prompt,
        )

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
