import asyncio
import json
import os
import yaml  # type: ignore
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# ⚡ ZERO-DEBT: Added missing LLM and Neurological imports
from litellm import acompletion, completion  # type: ignore
from System.core.paths import ROOT_DIR
from System.core.dna import AGENT_CONFIG
from System.neuroanatomy.systemic.endocrine import get_resolved_model
from System.llm import run_agent_async, get_system_context
from System.neuroanatomy.autonomic.interoception import (
    check_energy_levels,
    log_metabolism,
)
from System.neuroanatomy.autonomic.vestibular import commit_transaction, restore_balance
from System.neuroanatomy.systemic.immune_system import vault
from System.neuroanatomy.limbic.episodic import recall_recent_episodes, encode_episode

console = Console()


class WorkingMemory:
    """
    PFC Working Memory (Semantic Compressor).
    Maintains active pipeline state and autonomously compresses raw outputs
    into established facts to prevent quadratic token bleed.
    """

    def __init__(self, core_objective: str) -> None:
        self.core_objective = core_objective
        self.established_facts: list[str] = []
        self.recent_activity: list[str] = []
        # Rough token estimation (chars / 4). Threshold: ~3000 tokens
        self.compression_threshold_chars = 12000

    def add_event(self, agent_name: str, raw_output: str, actions: list[str]) -> None:
        """Adds a pipeline event to the working buffer."""
        event_log = f"[{agent_name} Output]:\n{raw_output}\nActions: {actions}"
        self.recent_activity.append(event_log)

    def get_current_context(self) -> str:
        """Returns the fully contextualized scratchpad for the next agent."""
        context = f"CORE OBJECTIVE: {self.core_objective}\n\n"
        if self.established_facts:
            context += "ESTABLISHED FACTS (Compressed Memory):\n"
            for fact in self.established_facts:
                context += f"- {fact}\n"
            context += "\n"

        if self.recent_activity:
            context += "RECENT PIPELINE ACTIVITY:\n"
            context += "\n\n".join(self.recent_activity)

        return context

    async def compress_if_bloated(self) -> None:
        """Autonomously distills recent activity if token limits are exceeded."""
        current_text = "\n".join(self.recent_activity)
        if len(current_text) < self.compression_threshold_chars:
            return

        console.print(
            "[dim magenta]🧠 PFC Buffer Full: Compressing working memory to save tokens...[/dim magenta]"
        )

        prompt = (
            "You are the Prefrontal Cortex. Synthesize the following pipeline activity into a highly "
            "concise, bulleted list of 'Established Facts' and 'Current State'. "
            "Discard all conversational filler and preserve ONLY technical facts, code paths, and outcomes.\n\n"
            f"ACTIVITY LOG:\n{current_text}"
        )

        try:
            model = AGENT_CONFIG.get("models", {}).get(
                "fast", "gemini/gemini-2.5-flash"
            )
            response = await acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                api_key=vault.get_api_key_for_model(model),
            )
            compressed_summary = response.choices[0].message.content.strip()

            self.established_facts.append(compressed_summary)
            self.recent_activity.clear()
            console.print(
                "[dim green]✅ Working memory successfully compressed.[/dim green]"
            )
        except Exception as e:
            console.print(f"[dim red]PFC Compression Failed: {e}[/dim red]")


class PrefrontalCortex:
    """
    The Seat of Consciousness (Executive Function).
    Holds Working Memory, consults Episodic Memory, decomposes complex goals,
    and supervises Swarm execution to prevent endless retry loops.
    """

    def __init__(self) -> None:
        self.working_memory: list[str] = []
        self.max_memory: int = 5

    def _remember(self, memory: str) -> None:
        self.working_memory.append(memory)
        if len(self.working_memory) > self.max_memory:
            self.working_memory.pop(0)

    def get_working_memory_context(self) -> str:
        if not self.working_memory:
            return "No previous steps executed."
        return "\n".join(f"- {mem}" for mem in self.working_memory)

    def decompose_goal(self, objective: str, past_experiences: str = "") -> list[str]:
        # ⚡ ZERO-DEBT: Biological bypass only when explicitly requested by legacy execution tests
        if os.environ.get("BRAIN_OS_BYPASS_PFC") == "1":
            return [objective]

        console.print(
            "[dim cyan]🧠 PFC: Consulting past experiences and decomposing objective...[/dim cyan]"
        )

        prompt = (
            "You are the Prefrontal Cortex of Brain OS. Your job is executive function and goal decomposition.\n"
            "Break the following objective down into a strict JSON list of 1 to 3 independent, actionable string commands.\n"
            "Review your PAST EXPERIENCES to avoid repeating historical mistakes or failed approaches.\n"
            "Do NOT use markdown fences. Return ONLY a valid JSON array of strings.\n\n"
            f"PAST EXPERIENCES:\n{past_experiences}\n\n"
            f"OBJECTIVE: {objective}"
        )

        try:
            model_name = AGENT_CONFIG.get("models", {}).get(
                "fast", "gemini/gemini-2.5-flash"
            )
            response = completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                api_key=vault.get_api_key_for_model(model_name),
            )
            raw_text = response.choices[0].message.content.strip()

            # Safe parsing block to avoid UI triggers
            if "```json" in raw_text:
                raw_text = raw_text.replace("```json", "")
            if "```" in raw_text:
                raw_text = raw_text.replace("```", "")

            tasks = json.loads(raw_text.strip())
            if isinstance(tasks, list) and all(isinstance(t, str) for t in tasks):
                return tasks
            return [objective]
        except Exception as e:
            console.print(
                f"[dim red]PFC Fallback (Decomposition bypassed): {str(e)}[/dim red]"
            )
            return [objective]

    async def execute_goal(
        self, objective: str, domain: str = "GENERAL", route: str = "WORKSPACE"
    ) -> str:
        from System.core.orchestrator import dispatch_task

        # 1. Recall past life experiences
        past_experiences = recall_recent_episodes()

        # 2. Decompose with historical context
        tasks = self.decompose_goal(objective, past_experiences)
        console.print(
            f"[bold cyan]🧠 PFC: Objective split into {len(tasks)} executive pulses.[/bold cyan]"
        )

        final_outcome = "Success"

        for i, pulse_desc in enumerate(tasks):
            console.print(
                f"\n[bold yellow]🧠 PFC Executive Pulse {i + 1}/{len(tasks)}[/bold yellow]"
            )

            context = self.get_working_memory_context()
            augmented_prompt = (
                f"GOAL: {objective}\n"
                f"DOMAIN/ROUTE PREFERENCE: {domain} / {route}\n"
                f"WORKING MEMORY (Previous context):\n{context}\n\n"
                f"CURRENT TASK: {pulse_desc}"
            )

            try:
                await dispatch_task(augmented_prompt)
                self._remember(f"Pulse {i + 1} Executed: {pulse_desc}")
            except Exception as e:
                console.print(
                    f"[bold red]❌ Swarm Failure on Step {i + 1}: {str(e)}[/bold red]"
                )
                final_outcome = f"Failed on Step {i + 1}: {str(e)}"
                break

        # 3. Form a permanent episodic memory of what just happened
        encode_episode(objective, tasks, final_outcome)

        return f"Consolidated {len(tasks)} pulses. Final state: {final_outcome}"


# 🧠 The Executive Pipeline Loop (Moved from runtime.py)
async def execute_pipeline(
    description: str, route_type: str, domain: str, resume_pipeline: list | None = None
) -> None:
    commit_transaction()

    tools_path = ROOT_DIR / "System" / "config" / "tools.yaml"
    with open(tools_path, "r", encoding="utf-8") as f:
        available_tools = yaml.safe_load(f)

    # ⚡ ZERO-DEBT: Use the injected resume state, or fetch a fresh one from DNA
    pipeline = (
        resume_pipeline
        if resume_pipeline is not None
        else list(AGENT_CONFIG.get("routes", {}).get(route_type, []))
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

                out_summary = f"--- {agent_name} Output ---\n{step_result.text}\nActions: {step_result.actions}"
                pfc_memory.add_event("Swarm Cohort", out_summary, [])

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
