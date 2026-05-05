import os
import re
import yaml  # type: ignore
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from litellm import completion  # type: ignore

from System.llm import run_agent, get_system_context

console = Console()

CONFIG_PATH = Path(__file__).parent / "config" / "agents.yaml"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        AGENT_CONFIG = yaml.safe_load(f)
except Exception:
    AGENT_CONFIG = {"agents": {}, "routes": {}, "models": {}}


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

    forbidden_targets = ["system/", ".env", "tools.py", "router.py", "cli.py"]
    for target in forbidden_targets:
        if target in prompt_lower:
            return (
                False,
                f"Hard Rule: Sandboxed. Cannot target '{target}'.",
                "NONE",
                "NONE",
                zero_usage,
            )

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


def execute_pipeline(description: str, route_type: str, domain: str) -> None:
    # Load Tools
    tools_path = Path(__file__).parent / "config" / "tools.yaml"
    with open(tools_path, "r", encoding="utf-8") as f:
        available_tools = yaml.safe_load(f)

    pipeline = list(AGENT_CONFIG["routes"].get(route_type, []))
    current_payload = description
    eval_retries = 0
    MAX_RETRIES = 1

    total_pipeline_tokens = 0
    agents_invoked = []
    pipeline_aborted = False

    while len(pipeline) > 0:
        step = pipeline.pop(0)
        agent_cfg = AGENT_CONFIG["agents"][step["agent"]]

        # ZERO-CONFIG MODEL FALLBACK
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

        total_pipeline_tokens += step_result.usage.get("total_tokens", 0)
        agents_invoked.append(agent_cfg["name"])

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

        # CIRCUIT BREAKERS
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

        # RETRY LOOP
        if step["agent"] == "auditor" and "[GRADE: FAIL]" in step_result.text:
            if eval_retries < MAX_RETRIES:
                console.print(
                    "\n[bold red]❌ Audit Failed! The Architect needs to fix the implementation.[/bold red]\n"
                )

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
                        "agent": "architect",
                        "tools": ["base", "write", "execute"],
                        "context": ["Meta", "Domain", "Studio"],
                    },
                )

                current_payload = f"Original Task: {description}\n\nCRITICAL - AUDIT FAILED. Read the critique, fix the code, and redeploy:\n\n{step_result.text}"
                eval_retries += 1
                continue
            else:
                console.print(
                    "\n[bold red]🛑 CIRCUIT BREAKER: Max eval retries reached. Halting pipeline.[/bold red]\n"
                )
                pipeline_aborted = True
                break

        current_payload = f"Original Task: {description}\n\nPrevious Agent ({agent_cfg['name']}) Output:\n{step_result.text}\n\nActions Taken:\n{step_result.actions}"

    # DIAGNOSTICS & LOGGING
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
