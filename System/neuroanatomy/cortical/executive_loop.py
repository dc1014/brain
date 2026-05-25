# --- System/neuroanatomy/cortical/executive_loop.py ---
import asyncio
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from System.core.paths import ROOT_DIR, normalize_path
from System.core.dna import get_dna_config
from System.neuroanatomy.systemic.endocrine import get_resolved_model
from System.llm import run_agent_async, get_system_context, compress_memory_buffer
from System.neuroanatomy.autonomic.interoception import (
    get_current_metabolism,
    log_metabolism,
    validate_metabolic_clearance,
)
from System.neuroanatomy.autonomic.vestibular import commit_transaction, restore_balance
from System.neuroanatomy.cortical.working_memory import (
    persist_pipeline_state,
    clear_pipeline_state,
    WorkingMemory,
)
from System.tools.diagnostic import render_pipeline_diagnostics

console = Console()


async def execute_swarm_cohort(
    swarm_steps: list[dict],
    current_payload: str,
    route_type: str,
    domain: str,
    is_exhausted: bool,
    available_tools: dict,
    pfc_memory: WorkingMemory,
    origin: str = "HUMAN",
) -> tuple[dict, list[str]]:
    swarm_metabolism = {}
    agents_invoked = []
    console.print(
        f"\n[bold magenta]Prefrontal Cortex: Spawning swarm of {len(swarm_steps)} agents in parallel...[/bold magenta]"
    )

    async def _task(sub_step):
        a_cfg = get_dna_config()["agents"][sub_step["agent"]]
        model_str = get_resolved_model(a_cfg["model"], is_exhausted)
        active_tools = [
            t
            for group in sub_step.get("tools", [])
            for t in available_tools.get(group, [])
        ]
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
            origin=origin,
        )
        return a_cfg["name"], model_str, res

    swarm_results = await asyncio.gather(*[_task(s) for s in swarm_steps])
    for agent_name, model_id, step_result in swarm_results:
        usage = getattr(step_result, "usage", {})
        p_tokens = (
            usage.get("prompt_tokens", 0)
            if isinstance(usage, dict)
            else getattr(usage, "prompt_tokens", 0)
        )
        c_tokens = (
            usage.get("completion_tokens", 0)
            if isinstance(usage, dict)
            else getattr(usage, "completion_tokens", 0)
        )

        if model_id not in swarm_metabolism:
            swarm_metabolism[model_id] = {"prompt": 0, "comp": 0}

        swarm_metabolism[model_id]["prompt"] += p_tokens
        swarm_metabolism[model_id]["comp"] += c_tokens

        await asyncio.to_thread(log_metabolism, p_tokens + c_tokens)

        agents_invoked.append(agent_name)
        display_text = step_result.text + (
            "\n\n**Actions Taken:**\n"
            + "\n".join([f"- {a}" for a in step_result.actions])
            if step_result.actions
            else ""
        )
        console.print(
            Panel(
                Markdown(display_text),
                title=f"[bold magenta]{agent_name} (Swarm Node)[/bold magenta]",
                border_style="magenta",
            )
        )
        pfc_memory.add_event(
            agent_name=agent_name,
            raw_output=step_result.text,
            actions=step_result.actions,
        )

    return swarm_metabolism, agents_invoked


async def execute_pipeline(
    description: str,
    route_type: str,
    domain: str,
    resume_pipeline: list | None = None,
    origin: str = "HUMAN",
) -> None:
    commit_transaction()
    available_tools = get_dna_config().get("tools", {})

    code_execution_enabled = os.environ.get(
        "CORETEX_ENABLE_CODE_EXECUTION", "false"
    ).lower() in ("true", "1", "yes")

    if not code_execution_enabled:
        restricted_tools = {
            "execute_in_sandbox",
            "execute_code",
            "run_terminal_command",
            "run_script",
            "deno_executor",
            "execute_command",
        }
        for group in available_tools:
            if isinstance(available_tools[group], list):
                available_tools[group] = [
                    t
                    for t in available_tools[group]
                    if (isinstance(t, str) and t not in restricted_tools)
                    or (isinstance(t, dict) and t.get("name") not in restricted_tools)
                ]
        console.print(
            "\n[dim yellow]Cognitive Pruning: Code execution tools hidden from active LLM context (Opt-In Required).[/dim yellow]"
        )

    pipeline = (
        resume_pipeline
        if resume_pipeline is not None
        else list(get_dna_config().get("routes", {}).get(route_type, []))
    )
    eval_retries: int = 0
    MAX_RETRIES: int = 1

    # ⚡ FIX: Sync the updated metabolism fetching hook
    metabolism_data = get_current_metabolism()
    is_exhausted = metabolism_data.get("exhausted", False)
    tokens_burned = metabolism_data.get("tokens_burned", 0)

    if is_exhausted:
        console.print(
            f"\n[bold yellow]Interoception Alert: System Exhausted ({tokens_burned:,} tokens burned). Downgrading cognitive load.[/bold yellow]"
        )

    session_metabolism = {}
    agents_invoked: list[str] = []
    pipeline_aborted = False
    pfc_memory = WorkingMemory(description)

    # ⚡ FIX: Explicitly type annotate the iterator to satisfy strict Mypy bounds
    current_state_idx: int = 0

    while current_state_idx < len(pipeline):
        persist_pipeline_state(
            description, route_type, domain, pipeline[current_state_idx:]
        )

        abort_flag = normalize_path(ROOT_DIR / "System" / ".vagus_abort_signal")
        if abort_flag.exists():
            console.print(
                "\n[bold red]Vagus Nerve Signal detected. Halting pipeline safely.[/bold red]"
            )
            pipeline_aborted = True
            abort_flag.unlink(missing_ok=True)
            break

        # ⚡ NEW GUARDRAIL: Halt if metabolic budget is exceeded mid-flight
        is_clear, clearance_reason = validate_metabolic_clearance()
        if not is_clear:
            console.print(
                f"\n[bold red]🛑 METABOLIC HALT: {clearance_reason}[/bold red]"
            )
            pipeline_aborted = True
            break

        step = pipeline[current_state_idx]
        current_payload = pfc_memory.get_current_context()

        MAX_CONTEXT_LENGTH = 45000
        if len(current_payload) > MAX_CONTEXT_LENGTH:
            console.print(
                f"[dim yellow]Token Economics: Context ceiling breached ({len(current_payload):,} chars). Pruning stale memories...[/dim yellow]"
            )
            current_payload = (
                current_payload[:4000]
                + "\n\n... [ OLDER EXECUTIONS PRUNED TO PRESERVE COGNITIVE EFFICIENCY ] ...\n\n"
                + current_payload[-40000:]
            )

        if "swarm" in step:
            swarm_metabolism, swarm_agents = await execute_swarm_cohort(
                step["swarm"],
                current_payload,
                route_type,
                domain,
                is_exhausted,
                available_tools,
                pfc_memory,
                origin,
            )
            for m_id, counts in swarm_metabolism.items():
                if m_id not in session_metabolism:
                    session_metabolism[m_id] = {"prompt": 0, "comp": 0}
                session_metabolism[m_id]["prompt"] += counts["prompt"]
                session_metabolism[m_id]["comp"] += counts["comp"]

            agents_invoked.extend(swarm_agents)

            overflow_text = pfc_memory.prune_and_get_overflow()
            if overflow_text:
                console.print(
                    "[dim magenta]PFC Buffer Full: Compressing working memory via fallback summary model...[/dim magenta]"
                )
                summary = await compress_memory_buffer(overflow_text)
                if summary:
                    pfc_memory.add_summary(summary)
                    console.print(
                        "[dim green]Working memory successfully compressed.[/dim green]"
                    )

            commit_transaction()
            console.print(
                "\n[bold green]Synaptic Consolidation: Swarm milestone committed to disk.[/bold green]"
            )
            continue

        agent_cfg = get_dna_config()["agents"][step["agent"]]
        model_str = get_resolved_model(agent_cfg["model"], is_exhausted)
        active_tools = [
            t for group in step.get("tools", []) for t in available_tools.get(group, [])
        ]
        full_system_prompt = agent_cfg["system_prompt"] + get_system_context(
            step.get("context", []), domain, prompt=current_payload
        )

        console.print(f"\n[bold cyan]{agent_cfg['name']} is working...[/bold cyan]")
        agents_invoked.append(agent_cfg["name"])

        step_result = await run_agent_async(
            role_name=agent_cfg["name"],
            model_string=model_str,
            system_prompt=full_system_prompt,
            user_prompt=current_payload,
            tools=active_tools if active_tools else None,
            route=route_type,
            domain=domain,
            origin=origin,
        )

        usage = getattr(step_result, "usage", {})
        p_tokens = (
            usage.get("prompt_tokens", 0)
            if isinstance(usage, dict)
            else getattr(usage, "prompt_tokens", 0)
        )
        c_tokens = (
            usage.get("completion_tokens", 0)
            if isinstance(usage, dict)
            else getattr(usage, "completion_tokens", 0)
        )

        if model_str not in session_metabolism:
            session_metabolism[model_str] = {"prompt": 0, "comp": 0}

        session_metabolism[model_str]["prompt"] += p_tokens
        session_metabolism[model_str]["comp"] += c_tokens
        await asyncio.to_thread(log_metabolism, p_tokens + c_tokens)

        display_text = step_result.text + (
            "\n\n**Actions Taken:**\n"
            + "\n".join([f"- {a}" for a in step_result.actions])
            if step_result.actions
            else ""
        )
        console.print(
            Panel(
                Markdown(display_text),
                title=f"[bold cyan]{agent_cfg['name']}[/bold cyan]",
                border_style="cyan",
            )
        )

        is_system_halt = "[SYSTEM HALT]" in step_result.text
        is_api_error = "API/Execution Error:" in step_result.text

        if is_system_halt or is_api_error:
            console.print(
                "\n[bold red]PIPELINE ABORTED via explicit exception response.[/bold red]"
            )
            pipeline_aborted = True
            break

        if agent_cfg.get("creates_milestone", True):
            commit_transaction()
            console.print(
                f"\n[dim green]Synaptic Consolidation: {agent_cfg['name']} milestone committed to disk.[/dim green]"
            )

        pfc_memory.add_event(agent_cfg["name"], step_result.text, step_result.actions)

        overflow_text = pfc_memory.prune_and_get_overflow()
        if overflow_text:
            console.print(
                "[dim magenta]PFC Buffer Full: Compressing working memory via fallback summary model...[/dim magenta]"
            )
            summary = await compress_memory_buffer(overflow_text)
            if summary:
                pfc_memory.add_summary(summary)
                console.print(
                    "[dim green]Working memory successfully compressed.[/dim green]"
                )

        if step["agent"] == "qa_auditor":
            from System.neuroanatomy.cortical.broca import validate_qa_audit

            is_valid, critique_msg = validate_qa_audit(step_result.text)

            if not is_valid:
                if eval_retries < MAX_RETRIES:
                    if "BROCA FORMATTING ERROR" in critique_msg:
                        console.print(
                            "\n[bold yellow]Broca's Area intercepted malformed JSON. Forcing retry.[/bold yellow]"
                        )
                    else:
                        console.print(
                            "\n[bold red]Audit Failed! The Product Manager needs to fix the code.[/bold red]\n"
                        )

                    if os.environ.get("BRAIN_OS_HEADLESS") == "1":
                        retry_auth = "y"
                    else:
                        try:
                            raw_auth = await asyncio.to_thread(
                                input, "Authorize autonomous retry? [Y/n]: "
                            )
                            retry_auth = raw_auth.strip().lower()
                        except (EOFError, KeyboardInterrupt):
                            retry_auth = "n"

                    if retry_auth in ["n", "no"]:
                        console.print(
                            "\n[bold red]Task Aborted: User declined autonomous retry.[/bold red]\n"
                        )
                        pipeline_aborted = True
                        break

                    pm_idx = next(
                        (
                            i
                            for i, s in enumerate(pipeline)
                            if s.get("agent") == "product_manager"
                        ),
                        0,
                    )
                    current_state_idx = pm_idx

                    pfc_memory.add_event("QA System", critique_msg, [])
                    eval_retries += 1
                    continue
                else:
                    console.print(
                        "\n[bold red]CIRCUIT BREAKER: Max eval retries reached. Halting pipeline.[/bold red]\n"
                    )
                    pipeline_aborted = True
                    break

        current_state_idx += 1

    render_pipeline_diagnostics(session_metabolism, eval_retries)

    log_dir = normalize_path(ROOT_DIR / "System" / "logs")
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    state_path = log_dir / "pipeline_state.md"

    if pipeline_aborted:
        restore_balance()
        console.print(
            "\n[bold red]Task Aborted. Environment safely rolled back.[/bold red]\n"
        )
        try:
            state_path.write_text("STATUS: ABORTED\n", encoding="utf-8")
        except OSError:
            pass
    else:
        commit_transaction()
        console.print("\n[bold green]Task Complete. Files committed.[/bold green]\n")
        try:
            state_path.write_text("STATUS: COMPLETE\n", encoding="utf-8")
        except OSError:
            pass

    clear_pipeline_state()
