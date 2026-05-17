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
from System.neuroanatomy.autonomic.interoception import (
    check_energy_levels,
    log_metabolism,
)
from System.llm import run_agent_async, get_system_context

# ⚡ ZERO-DEBT: Import the isolated OS DNA
from System.core.dna import AGENT_CONFIG
from System.neuroanatomy.systemic.endocrine import get_resolved_model

load_dotenv()

# 🛡️ IMMUNE SYSTEM: Engage the Nuclear Option (Scrub Environment)
vault.secure_environment()

console = Console()


async def execute_pipeline(
    description: str, route_type: str, domain: str, resume_pipeline: list | None = None
) -> None:
    from System.neuroanatomy.autonomic.vestibular import (
        commit_transaction,
        restore_balance,
    )
    from System.neuroanatomy.cortical.prefrontal import WorkingMemory

    commit_transaction()

    tools_path = ROOT_DIR / "System" / "config" / "tools.yaml"
    with open(tools_path, "r", encoding="utf-8") as f:
        available_tools = yaml.safe_load(f)

    # ⚡ ZERO-DEBT: Use the injected resume state, or fetch a fresh one from DNA
    pipeline = (
        resume_pipeline
        if resume_pipeline is not None
        else list(AGENT_CONFIG["routes"].get(route_type, []))
    )
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

    # 🧠 Initialize the Semantic Compressor Buffer
    pfc_memory = WorkingMemory(description)

    queue_file_path = ROOT_DIR / "System" / "execution_queue.json"

    while len(pipeline) > 0:
        # 💾 SHIFT-LEFT: Persist the active queue to disk to survive hard OS crashes
        with open(queue_file_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "original_task": description,
                    "route_type": route_type,
                    "domain": domain,
                    "remaining_steps": pipeline,
                },
                f,
                indent=2,
            )

        step = pipeline.pop(0)

        # Hydrate the input payload context dynamically from the PFC working memory
        current_payload = pfc_memory.get_current_context()

        # --- 🧠 PREFRONTAL CORTEX: Parallel Swarm Execution ---
        if "swarm" in step:
            swarm_steps = step["swarm"]
            console.print(
                f"\n[bold magenta]🧠 Prefrontal Cortex: Spawning swarm of {len(swarm_steps)} agents in parallel...[/bold magenta]"
            )

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
                await asyncio.to_thread(log_metabolism, step_tokens)
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

                # ⚡ ZERO-DEBT: Direct, non-interleaved logging to the PFC Semantic Compressor
                out_summary = f"--- {agent_name} Output ---\n{step_result.text}\nActions: {step_result.actions}"
                pfc_memory.add_event("Swarm Cohort", out_summary, [])

            # Autonomically evaluate memory weight and compress to block token leakage
            await pfc_memory.compress_if_bloated()

            commit_transaction()
            console.print(
                "\n[bold green]💾 Synaptic Consolidation: Swarm milestone committed to disk.[/bold green]"
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
        await asyncio.to_thread(log_metabolism, step_tokens)

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

        if agent_cfg.get("creates_milestone", True):
            commit_transaction()
            console.print(
                f"\n[dim green]💾 Synaptic Consolidation: {agent_cfg['name']} milestone committed to disk.[/dim green]"
            )

        # Update and myelinate current pipeline state transitions
        pfc_memory.add_event(agent_cfg["name"], step_result.text, step_result.actions)
        await pfc_memory.compress_if_bloated()

        # --- 🗣️ BROCA'S AREA (Data Contract Validation & RETRY LOOP) ---
        if step["agent"] == "qa_auditor":
            try:
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

                    # Inject error critiques straight into the semantic memory track
                    pfc_memory.add_event("QA System", critique_msg, [])
                    eval_retries += 1
                    continue
                else:
                    console.print(
                        "\n[bold red]🛑 CIRCUIT BREAKER: Max eval retries reached. Halting pipeline.[/bold red]\n"
                    )
                    pipeline_aborted = True
                    break

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

    # 🧹 LYMPHATIC SYSTEM: Clear the execution queue upon graceful termination
    if queue_file_path.exists():
        try:
            os.remove(queue_file_path)
        except OSError:
            pass
