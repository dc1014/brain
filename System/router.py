import typer
from dotenv import load_dotenv
from litellm import completion  # type: ignore
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Load the vault keys
load_dotenv()

# Initialize Typer and Rich Console
app = typer.Typer(help="Brain OS: The Multi-Agent Life Operating System")
console = Console()

# Define our specific agent models
ORCHESTRATOR: str = "gemini/gemini-2.5-flash"
WORKER: str = "anthropic/claude-haiku-4-5"
AUDITOR: str = "openai/gpt-4o-mini"


def run_agent(
    role_name: str, model_string: str, system_prompt: str, user_prompt: str
) -> str:
    # Notice we removed the hardcoded print() here because Typer handles the loading spinners now!
    try:
        response = completion(
            model=model_string,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return str(response.choices[0].message.content)
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

    # Step 1: Claude does the deep, structured work
    worker_system: str = "You are a highly structured system engineer. Break this task down into a clear, actionable step-by-step plan."

    with console.status(
        "[bold cyan]Worker (Claude) is thinking...[/bold cyan]", spinner="dots"
    ):
        claude_draft: str = run_agent(
            "Worker (Claude)", WORKER, worker_system, description
        )

    # Print Claude's output in a clean Markdown panel
    console.print(
        Panel(
            Markdown(claude_draft),
            title="[bold cyan]Worker (Claude)'s Draft[/bold cyan]",
            border_style="cyan",
        )
    )

    # Step 2: Gemini (Me) reviews and orchestrates the final output
    orchestrator_system: str = "You are the central orchestrator of a Life OS. Review the worker's plan. Summarize it into a final, polished 3-bullet-point executive summary."

    with console.status(
        "[bold magenta]Orchestrator (Gemini) is thinking...[/bold magenta]",
        spinner="dots",
    ):
        final_output: str = run_agent(
            "Orchestrator (Gemini)", ORCHESTRATOR, orchestrator_system, claude_draft
        )

    # Print Gemini's output
    console.print(
        Panel(
            Markdown(final_output),
            title="[bold magenta]Orchestrator (Gemini)'s Synthesis[/bold magenta]",
            border_style="magenta",
        )
    )
    console.print("\n[bold green]✅ Task Complete.[/bold green]\n")


if __name__ == "__main__":
    app()
