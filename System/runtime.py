import asyncio
import json
import os
import yaml  # type: ignore
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from dotenv import load_dotenv

from System.core.paths import ROOT_DIR
from System.neuroanatomy.systemic.immune_system import vault
from System.neuroanatomy.limbic.amygdala import scan_prompt
from System.neuroanatomy.autonomic.interoception import (
    check_energy_levels,
    log_metabolism,
)
from System.neuroanatomy.pathways.polymerase import (
    proofread_yaml_dna,
)
from System.llm import acompletion, run_agent_async, get_system_context

load_dotenv()

# 🛡️ IMMUNE SYSTEM: Engage the Nuclear Option (Scrub Environment)
vault.secure_environment()

console = Console()

CONFIG_DIR = ROOT_DIR / "System" / "config"
try:
    # 🧬 DNA POLYMERASE: Proofread the OS genetic code before booting
    proofread_yaml_dna(CONFIG_DIR)
    AGENT_CONFIG = {}
    for file in ["models.yaml", "agents.yaml", "routes.yaml"]:
        with open(CONFIG_DIR / file, "r", encoding="utf-8") as f:
            AGENT_CONFIG.update(yaml.safe_load(f))
except Exception as e:
    console.print(f"[bold red]BOOT WARNING: Config failed to load ({e}).[/bold red]")
    AGENT_CONFIG = {"agents": {}, "routes": {}, "models": {}}


async def analyze_task(prompt: str) -> tuple[bool, str, str, str, dict]:
    """Analyzes a user prompt using the Dispatcher to determine validity, routing, and domain context."""

    # --- 🦠 ENTERIC NERVOUS SYSTEM (Gut Reaction) ---
    from System.neuroanatomy.systemic.enteric import get_gut_reaction, save_gut_reaction

    # ⚡ SHIFT-LEFT: Prevent Async Blocking on File I/O
    gut_reflex = await asyncio.to_thread(get_gut_reaction, prompt)
    if gut_reflex:
        return gut_reflex
    zero_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # --- 1. THE AMYGDALA (Shift-Left Threat Detection) ---
    is_safe, threat_reason = await asyncio.to_thread(scan_prompt, prompt)
    if not is_safe:
        return False, threat_reason, "NONE", "NONE", zero_usage

    # --- 2. THE PREFRONTAL CORTEX (Dispatcher LLM) ---
    dispatcher_cfg = AGENT_CONFIG["agents"]["dispatcher"]
    system_prompt = dispatcher_cfg["system_prompt"] + get_system_context(
        ["Meta"], prompt=prompt
    )

    try:
        base_model = AGENT_CONFIG["models"][dispatcher_cfg["model"]]

        # 🧠 CORPUS CALLOSUM: Route Dispatcher (Analytical) to Left Brain
        from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere

        actual_model = route_hemisphere("DISPATCHER", base_model)

        response = await acompletion(
            model=actual_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            api_key=vault.get_api_key_for_model(actual_model),  # 🛡️ SECURE INJECTION
        )
        raw_text = str(response.choices[0].message.content).strip()

        usage_data = zero_usage.copy()
        if hasattr(response, "usage") and response.usage:
            usage_data["prompt_tokens"] = int(
                getattr(response.usage, "prompt_tokens", 0)
            )
            usage_data["completion_tokens"] = int(
                getattr(response.usage, "completion_tokens", 0)
            )
            usage_data["total_tokens"] = int(getattr(response.usage, "total_tokens", 0))

        if "REJECTED:" in raw_text.upper():
            reason = raw_text.upper().split("REJECTED:")[1].strip(" \"'}\n").strip()
            return False, reason, "NONE", "NONE", usage_data

        try:
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            data = json.loads(clean_text)
            route = str(data.get("route", "UNKNOWN")).strip().upper()
            domain = str(data.get("domain", "NONE")).strip()
        except json.JSONDecodeError:
            route = "UNKNOWN"
            domain = "NONE"

        # --- THE VAGUS NERVE: Log the Dispatcher's metabolism ---
        # ⚡ SHIFT-LEFT: Prevent Async Blocking
        await asyncio.to_thread(log_metabolism, usage_data.get("total_tokens", 0))

        # --- 🦠 ENTERIC NERVOUS SYSTEM (Save Memory) ---
        await asyncio.to_thread(
            save_gut_reaction, prompt, True, "Approved.", route, domain
        )

        return True, "Approved.", route, domain, usage_data

    except Exception as e:
        return False, f"Dispatcher API Error: {str(e)}", "NONE", "NONE", zero_usage


def get_resolved_model(desired_model_key: str, is_exhausted: bool) -> str:
    """Helper to resolve the fallback LLM models securely using the Vault."""
    if is_exhausted:
        from System.neuroanatomy.systemic.endocrine import is_cortisol_active

        if not is_cortisol_active():
            desired_model_key = "gpt_mini"

    desired_model_str = AGENT_CONFIG["models"].get(desired_model_key, "")

    # 🛡️ IMMUNE SYSTEM: Check the Secure Vault, not os.environ!
    if vault.get_api_key_for_model(desired_model_str):
        return desired_model_str

    if vault.get_api_key_for_model("openai/gpt"):
        return AGENT_CONFIG["models"].get("gpt_mini", "openai/gpt-4o-mini")
    elif vault.get_api_key_for_model("anthropic/claude"):
        return AGENT_CONFIG["models"].get("claude_haiku", "anthropic/claude-haiku-4-5")
    elif vault.get_api_key_for_model("gemini/"):
        return AGENT_CONFIG["models"].get("gemini_flash", "gemini/gemini-2.5-flash")

    return desired_model_str


async def execute_pipeline(description: str, route_type: str, domain: str) -> None:
    from System.neuroanatomy.autonomic.vestibular import (
        commit_transaction,
        restore_balance,
    )

    commit_transaction()

    tools_path = ROOT_DIR / "System" / "config" / "tools.yaml"
    with open(tools_path, "r", encoding="utf-8") as f:
        available_tools = yaml.safe_load(f)

    pipeline = list(AGENT_CONFIG["routes"].get(route_type, []))
    current_payload = description
    eval_retries = 0
    MAX_RETRIES = 1

    is_exhausted, tokens_burned = check_energy_levels()
    if is_exhausted:
        console.print(
            f"\n[bold yellow]⚠️ Interoception Alert: System Exhausted ({tokens_burned:,} tokens burned). Downgrading cognitive load.[/bold yellow]"
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

            swarm_results = await _execute_swarm_batch()

            for agent_name, step_result in swarm_results:
                step_tokens = step_result.usage.get("total_tokens", 0)
                total_pipeline_tokens += step_tokens
                await asyncio.to_thread(
                    log_metabolism, step_tokens
                )  # ⚡ Prevent Async Block
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

        console.print(f"\n[bold cyan]⏳ {agent_cfg['name']} is working...[/bold cyan]")
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
        await asyncio.to_thread(log_metabolism, step_tokens)  # ⚡ Prevent Async Block

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

        if (
            "[SYSTEM HALT]" in step_result.text
            or "API/Execution Error:" in step_result.text
        ):
            console.print("\n[bold red]🛑 PIPELINE ABORTED.[/bold red]")
            pipeline_aborted = True
            break

        # --- 🗣️ BROCA'S AREA (Data Contract Validation & RETRY LOOP) ---
        if step["agent"] == "qa_auditor":
            try:
                # ⚡ BULLETPROOF JSON PARSING
                clean_text = step_result.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:-3].strip()
                elif clean_text.startswith("```"):
                    clean_text = clean_text[3:-3].strip()

                data = json.loads(clean_text)
                audit_result = str(data.get("audit_result", "FAIL")).strip().upper()
                audit_reasoning = str(data.get("reasoning", "No reasoning provided."))
                is_valid = True
            except json.JSONDecodeError:
                is_valid = False
                audit_result = "FAIL"
                audit_reasoning = "JSON Parsing Failed. Hallucinated schema."

            if not is_valid or audit_result == "FAIL":
                if eval_retries < MAX_RETRIES:
                    if not is_valid:
                        console.print(
                            "\n[bold yellow]🗣️ Broca's Area intercepted malformed JSON. Forcing retry.[/bold yellow]"
                        )
                        critique_msg = "BROCA FORMATTING ERROR: You must strictly output valid JSON with 'audit_result': 'PASS' or 'FAIL'."
                    else:
                        console.print(
                            "\n[bold red]❌ Audit Failed! The Product Manager needs to fix the code.[/bold red]\n"
                        )
                        critique_msg = f"CRITICAL - AUDIT FAILED. Read the critique, fix the instructions, and redeploy:\n\n{audit_reasoning}"

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

                    current_payload = f"Original Task: {description}\n\n{critique_msg}"
                    eval_retries += 1
                    continue
                else:
                    console.print(
                        "\n[bold red]🛑 CIRCUIT BREAKER: Max eval retries reached. Halting pipeline.[/bold red]\n"
                    )
                    pipeline_aborted = True
                    break

        current_payload = f"Original Task: {description}\n\nPrevious Output:\n{step_result.text}\n\nActions Taken:\n{step_result.actions}"

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

    log_dir = ROOT_DIR / "logs"
    state_path = log_dir / "pipeline_state.md"

    if pipeline_aborted:
        restore_balance()
        console.print(
            "\n[bold red]🛑 Task Aborted. Environment safely rolled back.[/bold red]\n"
        )
        with open(state_path, "w", encoding="utf-8") as f:
            f.write("STATUS: ABORTED\n")
    else:
        commit_transaction()
        console.print("\n[bold green]✅ Task Complete. Files committed.[/bold green]\n")
        with open(state_path, "w", encoding="utf-8") as f:
            f.write("STATUS: COMPLETE\n")
