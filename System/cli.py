import json
import typer
import yaml  # type: ignore
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from litellm import completion  # type: ignore

from System.llm import LOG_FILE, LOG_DIR, log_interaction
from System.runtime import analyze_task, execute_pipeline
from System.tools import append_safe_file

app = typer.Typer(help="Brain OS: The Multi-Agent Life Operating System")
console = Console()

CONFIG_PATH = Path(__file__).parent / "config" / "agents.yaml"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        AGENT_CONFIG = yaml.safe_load(f)
except Exception as e:
    console.print(f"[bold red]Fatal Error loading agents.yaml:[/bold red] {e}")
    exit(1)


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
        f"[dim]✅ Pre-Flight Passed. Assigned Route: [bold]{route_type}[/bold] | Domain Context: [bold cyan]{domain}[/bold cyan][/dim]"
    )

    pipeline = list(AGENT_CONFIG["routes"].get(route_type, []))
    agents_to_run = [step["agent"] for step in pipeline]

    console.print("\n[bold yellow]⚠️  PIPELINE AUTHORIZATION[/bold yellow]")
    console.print(
        f"This task requires the [bold]{route_type}[/bold] route, which will wake up:"
    )
    console.print(f"[bold cyan]{' -> '.join(agents_to_run)}[/bold cyan]")

    try:
        auth = (
            input("\nAuthorize AI execution and token spend? [y/N]: ").strip().lower()
        )
    except (EOFError, KeyboardInterrupt):
        auth = "n"

    if auth not in ["y", "yes"]:
        console.print(
            "\n[bold red]🛑 Task Aborted: User declined pipeline execution.[/bold red]\n"
        )
        return

    # SHIFT-LEFT: Handoff to Process Manager
    execute_pipeline(description, route_type, domain)


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

    memory_path = Path(__file__).parent / "config" / "memory.yaml"
    with open(memory_path, "r", encoding="utf-8") as f:
        domains = yaml.safe_load(f).get("domains", {})

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
    console.print("\n[bold blue]🚀 Initializing Brain OS Vault...[/bold blue]")
    root_dir = Path(__file__).parent.parent

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
