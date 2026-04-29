import json
import typer
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion  # type: ignore
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Import our secure sandbox tool
from System.tools import write_safe_file

# Load the vault keys
load_dotenv()

# Initialize Typer and Rich Console
app = typer.Typer(help="Brain OS: The Multi-Agent Life Operating System")
console = Console()

# Define our specific agent models
ORCHESTRATOR: str = "gemini/gemini-2.5-flash"
WORKER: str = "anthropic/claude-haiku-4-5"
AUDITOR: str = "openai/gpt-4o-mini"

# Setup Logging Architecture
LOG_DIR: Path = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE: Path = LOG_DIR / "agent_interactions.jsonl"


def log_interaction(
    role_name: str,
    model_string: str,
    system_prompt: str,
    user_prompt: str,
    response_content: str,
    usage: dict,
) -> None:
    """Silently append a structured JSON log for every agent interaction."""
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
) -> str:
    """Core function to ping the LLM APIs, execute tools, and log the results."""
    try:
        # Build the dynamic arguments for the API call
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

        # Capture standard text content (if any)
        content: str = str(message.content or "")

        # --- TOOL EXECUTION INTERCEPTOR ---
        if hasattr(message, "tool_calls") and message.tool_calls:
            console.print(f"\n[dim]⚡ {role_name} is using tools...[/dim]")
            for tool_call in message.tool_calls:
                if tool_call.function.name == "write_safe_file":
                    args = json.loads(tool_call.function.arguments)
                    filepath = args.get("filepath", "")
                    file_content = args.get("content", "")

                    # Physically execute the tool on your machine!
                    result = write_safe_file(filepath, file_content)

                    console.print(f"[dim]💾 Tool Result: {result}[/dim]")
                    content += f"\n\n**System Action:** `{result}`"

        # Extract standard token usage cleanly for JSON logs
        usage_data: dict = {}
        if hasattr(response, "usage") and response.usage:
            usage_data = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }

        # Write the audit trail
        log_interaction(
            role_name, model_string, system_prompt, user_prompt, content, usage_data
        )

        return content
    except Exception as e:
        return f"Error: {str(e)}"


@app.command()
def task(
    description: str = typer.Argument(..., help="The task you want the AI to perform."),
) -> None:
    """
    Execute a complex task using the Multi-Agent Trinity.
    """
    console.print(
        f"\n[bold green]🚀 Initializing Life OS task:[/bold green] '{description}'\n"
    )

    # --- DEFINING THE JSON SCHEMA ---
    # Minified to save input tokens. No poetry, just strict types.
    write_file_tool = [
        {
            "type": "function",
            "function": {
                "name": "write_safe_file",
                "description": "Writes content to a file. Allowed zones: Personal/, Professional/, Studio/.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path relative to root. Ex: 'Professional/ideas.md'",
                        },
                        "content": {
                            "type": "string",
                            "description": "The full text content to write to the file.",
                        },
                    },
                    "required": ["filepath", "content"],
                },
            },
        }
    ]

    # Step 1: Claude does the deep, structured work (Now with Tools!)
    worker_system: str = "You are a highly structured system engineer. Break this task down into a clear plan. If appropriate, use your tools to generate and save the required files."

    with console.status(
        "[bold cyan]Worker (Claude) is thinking...[/bold cyan]", spinner="dots"
    ):
        claude_draft: str = run_agent(
            "Worker (Claude)", WORKER, worker_system, description, tools=write_file_tool
        )

    console.print(
        Panel(
            Markdown(claude_draft),
            title="[bold cyan]Worker (Claude)'s Draft & Actions[/bold cyan]",
            border_style="cyan",
        )
    )

    # Step 2: Gemini (Me) reviews and orchestrates the final output
    orchestrator_system: str = "You are the central orchestrator of a Life OS. Review the worker's plan and the files it created. Summarize it into a final, polished executive summary."

    with console.status(
        "[bold magenta]Orchestrator (Gemini) is thinking...[/bold magenta]",
        spinner="dots",
    ):
        final_output: str = run_agent(
            "Orchestrator (Gemini)", ORCHESTRATOR, orchestrator_system, claude_draft
        )

    console.print(
        Panel(
            Markdown(final_output),
            title="[bold magenta]Orchestrator (Gemini)'s Synthesis[/bold magenta]",
            border_style="magenta",
        )
    )
    console.print("\n[bold green]✅ Task Complete.[/bold green]\n")


@app.command()
def logs(
    limit: int = typer.Option(3, help="Number of recent interactions to display."),
) -> None:
    """View the most recent agent interactions in a human-readable format."""
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
        meta_text = f"[bold cyan]Agent:[/bold cyan] {data['agent']}\n"
        meta_text += f"[bold cyan]Model:[/bold cyan] {data['model']}\n"
        meta_text += f"[bold cyan]Time:[/bold cyan] {data['timestamp']}\n"
        meta_text += f"[bold cyan]Tokens:[/bold cyan] {data.get('tokens', {})}"

        console.print(
            Panel(meta_text, title="Interaction Metadata", border_style="cyan")
        )
        console.print(
            Panel(Markdown(data["response"]), title="AI Response", border_style="white")
        )
        console.print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    app()
