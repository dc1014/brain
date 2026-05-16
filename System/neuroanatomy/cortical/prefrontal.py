import json
from rich.console import Console
from litellm import completion  # type: ignore

from System.runtime import AGENT_CONFIG

console = Console()


class PrefrontalCortex:
    """
    The Seat of Consciousness (Executive Function).
    Holds Working Memory, decomposes complex goals, and supervises Swarm execution
    to prevent endless retry loops and hallucination cascades.
    """

    def __init__(self) -> None:
        self.working_memory: list[str] = []
        self.max_memory: int = 5

    def _remember(self, memory: str) -> None:
        """Encodes short-term actions into Working Memory."""
        self.working_memory.append(memory)
        if len(self.working_memory) > self.max_memory:
            self.working_memory.pop(0)

    def get_working_memory_context(self) -> str:
        """Retrieves the active session's context window."""
        if not self.working_memory:
            return "No previous steps executed."
        return "\n".join(f"- {mem}" for mem in self.working_memory)

    def decompose_goal(self, objective: str) -> list[str]:
        """Breaks a monolithic goal into actionable, sequential sub-tasks."""
        console.print("[dim cyan]🧠 PFC: Decomposing complex objective...[/dim cyan]")

        prompt = (
            "You are the Prefrontal Cortex of Brain OS. Your job is executive function and goal decomposition.\n"
            "Break the following objective down into a strict JSON list of 1 to 3 independent, actionable string commands.\n"
            "Do NOT use markdown fences. Return ONLY a valid JSON array of strings.\n\n"
            f"OBJECTIVE: {objective}"
        )

        try:
            model_name = AGENT_CONFIG.get("models", {}).get(
                "fast", "gemini/gemini-2.0-flash"
            )
            response = completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw_text = response.choices[0].message.content.strip()

            # Clean up markdown fences if the LLM disobeys the prompt
            if "```" in raw_text:
                raw_text = raw_text.split("```")[-2].replace("json", "").strip()

            tasks = json.loads(raw_text)
            return [str(t) for t in tasks] if isinstance(tasks, list) else [objective]
        except Exception as e:
            console.print(
                f"[dim red]🧠 PFC Decomposition Error: {e}. Falling back to monolithic execution.[/dim red]"
            )
            return [objective]

    async def execute_goal(
        self, objective: str, domain: str = "GENERAL", route: str = "WORKSPACE"
    ) -> str:
        """
        Orchestrates sequential Swarm pulses based on a decomposed goal.
        Passes Working Memory context between steps to maintain objective coherence.
        """
        from System.core.orchestrator import dispatch_task

        tasks = self.decompose_goal(objective)
        console.print(
            f"[bold cyan]🧠 PFC: Objective split into {len(tasks)} executive pulses.[/bold cyan]"
        )

        for i, pulse_desc in enumerate(tasks):
            console.print(
                f"\n[bold yellow]🧠 PFC Executive Pulse {i + 1}/{len(tasks)}[/bold yellow]"
            )

            # Inject Working Memory and CLI preferences into the pulse
            context = self.get_working_memory_context()
            augmented_prompt = (
                f"GOAL: {objective}\n"
                f"DOMAIN/ROUTE PREFERENCE: {domain} / {route}\n"
                f"WORKING MEMORY (Previous context):\n{context}\n\n"
                f"CURRENT TASK: {pulse_desc}"
            )

            # Execute the pulse via the standard CNS dispatcher
            await dispatch_task(augmented_prompt)

            # Update Working Memory with the "Enactment" of this pulse
            self._remember(f"Pulse {i + 1} Executed: {pulse_desc}")

        return (
            f"Successfully consolidated {len(tasks)} pulses into the objective reality."
        )
