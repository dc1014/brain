import asyncio
import os
import yaml  # type: ignore
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from System.organs.amygdala import scan_prompt
from System.organs.interoception import check_energy_levels, log_metabolism


from System.llm import run_agent_async, get_system_context

console = Console()

CONFIG_PATH = Path(__file__).parent / "config" / "agents.yaml"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        AGENT_CONFIG = yaml.safe_load(f)
except Exception:
    AGENT_CONFIG = {"agents": {}, "routes": {}, "models": {}}


async def analyze_task(prompt: str) -> tuple[bool, str, str, str, dict]:
    """Analyzes a user prompt using the Dispatcher to determine validity, routing, and domain context."""

    # --- 🦠 ENTERIC NERVOUS SYSTEM (Gut Reaction) ---
    from System.organs.enteric import get_gut_reaction, save_gut_reaction

    gut_reflex = get_gut_reaction(prompt)
    if gut_reflex:
        return gut_reflex
    zero_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # --- 1. THE AMYGDALA (Shift-Left Threat Detection) ---
    is_safe, threat_reason = scan_prompt(prompt)
    if not is_safe:
        return False, threat_reason, "NONE", "NONE", zero_usage

    # --- 2. THE PREFRONTAL CORTEX (Dispatcher LLM) ---
    dispatcher_cfg = AGENT_CONFIG["agents"]["dispatcher"]
    system_prompt = dispatcher_cfg["system_prompt"] + get_system_context(
        ["Meta"], prompt=prompt
    )

    from litellm import acompletion

    try:
        response = await acompletion(
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

        # --- THE VAGUS NERVE: Log the Dispatcher's metabolism ---
        from System.organs.interoception import log_metabolism

        log_metabolism(usage_data.get("total_tokens", 0))

        # --- 🦠 ENTERIC NERVOUS SYSTEM (Save Memory) ---
        from System.organs.enteric import save_gut_reaction

        save_gut_reaction(prompt, True, "Approved.", route, domain)

        return True, "Approved.", route, domain, usage_data

    except Exception as e:
        return False, f"Dispatcher API Error: {str(e)}", "NONE", "NONE", zero_usage


def get_resolved_model(desired_model_key: str, is_exhausted: bool) -> str:
    """Helper to resolve the fallback LLM models cleanly."""
    import os

    if is_exhausted:
        from System.organs.endocrine import is_cortisol_active

        if not is_cortisol_active():
            desired_model_key = "gpt_mini"

    env_key_map = {
        "gpt_mini": "OPENAI_API_KEY",
        "claude_haiku": "ANTHROPIC_API_KEY",
        "gemini_flash": "GEMINI_API_KEY",
        "claude_sonnet": "ANTHROPIC_API_KEY",
    }

    if os.getenv(env_key_map.get(desired_model_key, "")):
        return AGENT_CONFIG["models"][desired_model_key]

    if os.getenv("OPENAI_API_KEY"):
        return AGENT_CONFIG["models"]["gpt_mini"]
    elif os.getenv("ANTHROPIC_API_KEY"):
        return AGENT_CONFIG["models"]["claude_haiku"]
    elif os.getenv("GEMINI_API_KEY"):
        return AGENT_CONFIG["models"]["gemini_flash"]
    return AGENT_CONFIG["models"][desired_model_key]


async def execute_pipeline(description: str, route_type: str, domain: str) -> None:
    from System.organs.vestibular import commit_transaction, restore_balance

    commit_transaction()

    tools_path = Path(__file__).parent / "config" / "tools.yaml"
    with open(tools_path, "r", encoding="utf-8") as f:
        available_tools = yaml.safe_load(f)

    pipeline = list(AGENT_CONFIG["routes"].get(route_type, []))
    current_payload = description
    eval_retries = 0
    MAX_RETRIES = 1

    is_exhausted, tokens_burned = check_energy_levels()
    if is_exhausted:
        console.print(
            f"\\n[bold yellow]⚠️ Interoception Alert: System Exhausted ({tokens_burned:,} tokens burned). Downgrading cognitive load.[/bold yellow]"
        )

    total_pipeline_tokens = 0
    agents_invoked: list[str] = []
    pipeline_aborted = False

    while len(pipeline) > 0:
        step = pipeline.pop(0)

        # --- 🧠 PREFRONTAL CORTEX: Parallel Swarm Execution ---
        if "swarm" in step:
            swarm_steps = step["swarm"]
            console.print(
                f"\n[bold magenta]🧠 Prefrontal Cortex: Spawning swarm of {len(swarm_steps)} agents in parallel...[/bold magenta]"
            )

            swarm_outputs = []

            async def _execute_swarm_batch():
                async def _task(sub_step):
                    a_cfg = AGENT_CONFIG["agents"][sub_step["agent"]]
                    model_str = get_resolved_model(a_cfg["model"], is_exhausted)

                    active_tools = []
                    for t_group in sub_step.get("tools", []):
                        active_tools.extend(available_tools.get(t_group, []))

                    full_sys_prompt = a_cfg["system_prompt"] + get_system_context(
                        sub_step.get("context", []), domain, prompt=current_payload
                    )

                    res = await run_agent_async(
                        role_name=a_cfg["name"],
                        model_string=model_str,
                        system_prompt=full_sys_prompt,
                        user_prompt=current_payload,
                        tools=active_tools if active_tools else None,
                        route=route_type,
                        domain=domain,
                    )
                    return a_cfg["name"], res

                return await asyncio.gather(*[_task(s) for s in swarm_steps])

            # STAGE 2: Await natively!
            swarm_results = await _execute_swarm_batch()

            for agent_name, step_result in swarm_results:
                step_tokens = step_result.usage.get("total_tokens", 0)
                total_pipeline_tokens += step_tokens
                log_metabolism(step_tokens)
                agents_invoked.append(agent_name)

                display_text = step_result.text
                if step_result.actions:
                    display_text += "\n\n**Actions Taken:**\n" + "\n".join(
                        [f"- {a}" for a in step_result.actions]
                    )

                console.print(
                    Panel(
                        Markdown(display_text),
                        title=f"[bold magenta]🐝 {agent_name} (Swarm Node)[/bold magenta]",
                        border_style="magenta",
                    )
                )
                swarm_outputs.append(
                    f"--- {agent_name} Output ---\n{step_result.text}\nActions: {step_result.actions}"
                )

            current_payload = (
                f"Original Task: {description}\n\nSwarm Operations Complete:\n"
                + "\n\n".join(swarm_outputs)
            )
            continue

        # --- 🚂 STANDARD LINEAR EXECUTION ---
        agent_cfg = AGENT_CONFIG["agents"][step["agent"]]
        model_str = get_resolved_model(agent_cfg["model"], is_exhausted)

        active_tools = []
        for t_group in step.get("tools", []):
            active_tools.extend(available_tools.get(t_group, []))

        full_system_prompt = agent_cfg["system_prompt"] + get_system_context(
            step.get("context", []), domain, prompt=current_payload
        )

        console.print(f"\\n[bold cyan]⏳ {agent_cfg['name']} is working...[/bold cyan]")
        agents_invoked.append(agent_cfg["name"])

        step_result = await run_agent_async(
            role_name=agent_cfg["name"],
            model_string=model_str,
            system_prompt=full_system_prompt,
            user_prompt=current_payload,
            tools=active_tools if active_tools else None,
            route=route_type,
            domain=domain,
        )

        step_tokens = step_result.usage.get("total_tokens", 0)
        total_pipeline_tokens += step_tokens
        log_metabolism(step_tokens)

        display_text = step_result.text
        if step_result.actions:
            display_text += "\\n\\n**Actions Taken:**\\n" + "\\n".join(
                [f"- {a}" for a in step_result.actions]
            )

        console.print(
            Panel(
                Markdown(display_text),
                title=f"[bold cyan]{agent_cfg['name']}[/bold cyan]",
                border_style="cyan",
            )
        )

        if (
            "[SYSTEM HALT]" in step_result.text
            or "API/Execution Error:" in step_result.text
        ):
            console.print("\\n[bold red]🛑 PIPELINE ABORTED.[/bold red]")
            pipeline_aborted = True
            break

        # --- 🗣️ BROCA'S AREA (Data Contract Validation & RETRY LOOP) ---
        if step["agent"] == "qa_auditor":
            from System.organs.broca import enforce_data_contract

            is_valid, audit_content = enforce_data_contract(
                step_result.text, "audit_result"
            )

            if (
                not is_valid
                or "FAIL" in audit_content.upper()
                or '<audit_result grade="FAIL">' in step_result.text
            ):
                if eval_retries < MAX_RETRIES:
                    if not is_valid:
                        console.print(
                            "\\n[bold yellow]🗣️ Broca's Area intercepted malformed XML. Forcing retry.[/bold yellow]"
                        )
                        critique_msg = f"BROCA FORMATTING ERROR: {audit_content}\\nYou must strictly output <audit_result>PASS</audit_result> or <audit_result>FAIL</audit_result>."
                    else:
                        console.print(
                            "\\n[bold red]❌ Audit Failed! The Product Manager needs to fix the code.[/bold red]\\n"
                        )
                        critique_msg = f"CRITICAL - AUDIT FAILED. Read the critique, fix the instructions, and redeploy:\\n\\n{step_result.text}"

                    if os.environ.get("BRAIN_OS_HEADLESS") == "1":
                        retry_auth = "y"
                    else:
                        try:
                            retry_auth = (
                                input("Authorize autonomous retry? [Y/n]: ")
                                .strip()
                                .lower()
                            )
                        except (EOFError, KeyboardInterrupt):
                            retry_auth = "n"

                    if retry_auth in ["n", "no"]:
                        console.print(
                            "\n[bold red]🛑 Task Aborted: User declined autonomous retry.[/bold red]\n"
                        )
                        pipeline_aborted = True
                        break

                    # Re-insert the failing step, but we fall back to the linear PM to fix the Swarm's mess
                    pipeline.insert(
                        0,
                        {
                            "agent": "qa_auditor",
                            "tools": ["base"],
                            "context": ["Meta", "Domain", "Studio"],
                        },
                    )
                    pipeline.insert(
                        0,
                        {
                            "agent": "product_manager",
                            "tools": ["base", "write", "execute", "sense_environment"],
                            "context": ["Meta", "Domain", "Studio"],
                        },
                    )

                    current_payload = (
                        f"Original Task: {description}\\n\\n{critique_msg}"
                    )
                    eval_retries += 1
                    continue
                else:
                    console.print(
                        "\\n[bold red]🛑 CIRCUIT BREAKER: Max eval retries reached. Halting pipeline.[/bold red]\\n"
                    )
                    pipeline_aborted = True
                    break

        current_payload = f"Original Task: {description}\\n\\nPrevious Output:\\n{step_result.text}\\n\\nActions Taken:\\n{step_result.actions}"

    agent_summary = ", ".join(
        [f"{agent} (x{agents_invoked.count(agent)})" for agent in set(agents_invoked)]
    )
    diagnostics = (
        f"[bold cyan]Agents Invoked:[/bold cyan] {agent_summary}\\n"
        f"[bold cyan]Eval Loops (Retries):[/bold cyan] {eval_retries}\\n"
        f"[bold cyan]Total Tokens Burned:[/bold cyan] {total_pipeline_tokens:,}"
    )
    console.print(
        Panel(
            diagnostics,
            title="[bold green]📊 Pipeline Diagnostics[/bold green]",
            border_style="green",
        )
    )

    log_dir = Path(__file__).parent.parent / "logs"
    state_path = log_dir / "pipeline_state.md"

    if pipeline_aborted:
        restore_balance()
        console.print(
            "\\n[bold red]🛑 Task Aborted. Environment safely rolled back.[/bold red]\\n"
        )
        with open(state_path, "w", encoding="utf-8") as f:
            f.write("STATUS: ABORTED\\n")
    else:
        commit_transaction()
        console.print(
            "\\n[bold green]✅ Task Complete. Files committed.[/bold green]\\n"
        )
        with open(state_path, "w", encoding="utf-8") as f:
            f.write("STATUS: COMPLETE\\n")
