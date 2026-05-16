import json
from rich.console import Console
from litellm import completion  # type: ignore

from System.runtime import AGENT_CONFIG
from System.neuroanatomy.limbic.episodic import recall_recent_episodes, encode_episode

console = Console()


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
        import os

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
