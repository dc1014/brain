import json
import os
import re
import typer
import yaml  # type: ignore
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion  # type: ignore
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from System.llm import run_agent, log_interaction, get_system_context, LOG_FILE, LOG_DIR

from System.tools import (
    append_safe_file,
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
        f"[dim]✅ Pre-Flight Passed. Assigned Route: [bold]{route_type}[/bold] | Domain Context: [bold cyan]{domain}[/bold cyan][/dim]"
    )

    # --- SHIFT-LEFT: TOKEN ECONOMICS AUTHORIZATION ---
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

    # --- SHIFT-LEFT: DECLARATIVE TOOL LOADING ---
    tools_path = Path(__file__).parent / "config" / "tools.yaml"
    with open(tools_path, "r", encoding="utf-8") as f:
        available_tools = yaml.safe_load(f)

    # --- EXECUTE DECLARATIVE PIPELINE ---
    pipeline = AGENT_CONFIG["routes"].get(route_type, [])
    current_payload = description

    # --- EXECUTE DECLARATIVE PIPELINE ---
    # --- EXECUTE DECLARATIVE PIPELINE ---
    pipeline = list(AGENT_CONFIG["routes"].get(route_type, []))
    current_payload = description
    eval_retries = 0
    MAX_RETRIES = 1

    # SHIFT-LEFT: Initialize Pipeline Metrics
    total_pipeline_tokens = 0
    agents_invoked = []
    pipeline_aborted = False

    while len(pipeline) > 0:
        step = pipeline.pop(0)
        agent_cfg = AGENT_CONFIG["agents"][step["agent"]]

        # --- ZERO-CONFIG MODEL FALLBACK ---
        desired_model_key = agent_cfg["model"]
        env_key_map = {
            "gpt_mini": "OPENAI_API_KEY",
            "claude_haiku": "ANTHROPIC_API_KEY",
            "gemini_flash": "GEMINI_API_KEY",
            "claude_sonnet": "ANTHROPIC_API_KEY",
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

        console.print(f"\n[bold cyan]⏳ {agent_cfg['name']} is working...[/bold cyan]")

        step_result = run_agent(
            role_name=agent_cfg["name"],
            model_string=model_str,
            system_prompt=full_system_prompt,
            user_prompt=current_payload,
            tools=active_tools if active_tools else None,
            route=route_type,
            domain=domain,
        )

        # Update Metrics
        total_pipeline_tokens += step_result.usage.get("total_tokens", 0)
        agents_invoked.append(agent_cfg["name"])

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

        # --- SHIFT-LEFT: FATAL ERROR CIRCUIT BREAKERS ---
        if "[SYSTEM HALT]" in step_result.text:
            console.print(
                "\n[bold red]🛑 PIPELINE ABORTED: Security clearance denied by user.[/bold red]"
            )
            pipeline_aborted = True
            break

        if "API/Execution Error:" in step_result.text:
            console.print(
                "\n[bold red]🛑 PIPELINE ABORTED: Fatal API or Execution Error.[/bold red]"
            )
            pipeline_aborted = True
            break

        # --- LAYER 2 EVALUATION LOOP ---
        if step["agent"] == "auditor" and "[GRADE: FAIL]" in step_result.text:
            if eval_retries < MAX_RETRIES:
                console.print(
                    "\n[bold red]❌ Audit Failed! The Architect needs to fix the implementation.[/bold red]\n"
                )

                # --- SHIFT-LEFT: RETRY AUTHORIZATION ---
                try:
                    retry_auth = (
                        input("Authorize autonomous retry? [Y/n]: ").strip().lower()
                    )
                except (EOFError, KeyboardInterrupt):
                    retry_auth = "n"

                if retry_auth in ["n", "no"]:
                    console.print(
                        "\n[bold red]🛑 Task Aborted: User declined autonomous retry.[/bold red]\n"
                    )
                    pipeline_aborted = True
                    break
                # ---------------------------------------

                pipeline.insert(
                    0,
                    {
                        "agent": "auditor",
                        "tools": ["base", "write"],
                        "context": ["Meta", "Domain", "Studio"],
                    },
                )
                pipeline.insert(
                    0,
                    {
                        "agent": "architect",  # <-- FIXED: Was previously 'engineer'
                        "tools": ["base", "write", "execute"],
                        "context": ["Meta", "Domain", "Studio"],
                    },
                )

                # Preserve the original task context so the Architect doesn't get lost
                current_payload = f"Original Task: {description}\n\nCRITICAL - AUDIT FAILED. Read the critique, fix the code, and redeploy:\n\n{step_result.text}"
                eval_retries += 1
                continue
            else:
                console.print(
                    "\n[bold red]🛑 CIRCUIT BREAKER: Max eval retries reached. Halting pipeline.[/bold red]\n"
                )
                pipeline_aborted = True
                break

        # Hand-off Pipeline Payload (Normal flow)
        current_payload = f"Original Task: {description}\n\nPrevious Agent ({agent_cfg['name']}) Output:\n{step_result.text}\n\nActions Taken:\n{step_result.actions}"

    # --- PIPELINE DIAGNOSTICS DISPLAY ---
    agent_summary = ", ".join(
        [f"{agent} (x{agents_invoked.count(agent)})" for agent in set(agents_invoked)]
    )
    diagnostics = (
        f"[bold cyan]Agents Invoked:[/bold cyan] {agent_summary}\n"
        f"[bold cyan]Eval Loops (Retries):[/bold cyan] {eval_retries}\n"
        f"[bold cyan]Total Tokens Burned:[/bold cyan] {total_pipeline_tokens:,}"
    )
    console.print(
        Panel(
            diagnostics,
            title="[bold green]📊 Pipeline Diagnostics[/bold green]",
            border_style="green",
        )
    )

    # SHIFT-LEFT: Graceful Abort Logging
    root_dir = Path(__file__).parent.parent
    log_dir = root_dir / "logs"
    state_path = log_dir / "pipeline_state.md"

    if pipeline_aborted:
        console.print("\n[bold red]🛑 Task Aborted.[/bold red]\n")
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            f.write(
                "STATUS: ABORTED\nREASON: Pipeline hit a critical circuit breaker (Security Halt, API Failure, or Max Retries).\n"
            )
    else:
        console.print("\n[bold green]✅ Task Complete.[/bold green]\n")
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            f.write("STATUS: COMPLETE\nREASON: Terminal state reached.\n")


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
