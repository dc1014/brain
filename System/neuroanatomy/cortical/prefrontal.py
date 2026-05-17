import json
import os
from rich.console import Console
from litellm import completion  # type: ignore

from System.llm import acompletion
from System.runtime import AGENT_CONFIG
from System.neuroanatomy.limbic.episodic import recall_recent_episodes, encode_episode
from System.neuroanatomy.systemic.immune_system import vault

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
