import asyncio
import json
import os
import re
from rich.console import Console
from litellm import acompletion  # type: ignore

# ⚡ TECH DEBT RESOLVED: Consolidated split paths imports into a unified entry point
from System.core.dna import get_dna_config
from System.neuroanatomy.autonomic.interoception import (
    log_metabolism,
)
from System.neuroanatomy.systemic.immune_system import vault
from System.neuroanatomy.limbic.episodic import recall_recent_episodes, encode_episode

console = Console()


class PrefrontalCortex:
    """The Seat of Consciousness (Executive Function)."""

    def __init__(self) -> None:
        # ⚡ SEMANTIC FIX: Renamed from working_memory to pulse_history to resolve name collisions
        self.pulse_history: list[str] = []
        self.max_memory: int = 5

    def _clean_json_payload(self, raw_text: str) -> str:
        """Surgically strips markdown blocks and XML wrappers from raw string responses."""
        xml_match = re.search(r"<tasks_json>(.*?)</tasks_json>", raw_text, re.DOTALL)
        clean_str = xml_match.group(1).strip() if xml_match else raw_text

        # Use regex substitution to elegantly wipe out markdown fencing noise
        clean_str = re.sub(r"```json\s*", "", clean_str, flags=re.IGNORECASE)
        clean_str = re.sub(r"```\s*", "", clean_str)
        clean_str = clean_str.strip()

        if not clean_str.startswith("["):
            array_match = re.search(r"\[\s*\".*?\"\s*\]", clean_str, re.DOTALL)
            if array_match:
                clean_str = array_match.group(0)
        return clean_str

    def _remember(self, memory: str) -> None:
        self.pulse_history.append(memory)
        if len(self.pulse_history) > self.max_memory:
            self.pulse_history.pop(0)

    def get_working_memory_context(self) -> str:
        if not self.pulse_history:
            return "No previous steps executed."
        return "\n".join(f"- {mem}" for mem in self.pulse_history)

    # ⚡ ASYNC FIX: Promoted to async def to eliminate blocking network thread I/O states
    async def decompose_goal(
        self, objective: str, past_experiences: str = ""
    ) -> list[str]:
        if os.environ.get("BRAIN_OS_BYPASS_PFC") == "1":
            return [objective]

        console.print(
            "[dim cyan]🧠 PFC: Consulting past experiences and decomposing objective...[/dim cyan]"
        )
        prompt = (
            "You are the Prefrontal Cortex of CoreTex OS. Your job is executive function and goal decomposition.\n"
            "Break the following objective down into a strict JSON list of 1 to 3 independent, actionable string commands.\n"
            "CRITICAL PROTOCOL: If the task is a simple, single-step action (e.g., writing a file, running a single script, answering a question), you MUST output exactly ONE command in the array. DO NOT overcomplicate it. Only use 2 or 3 steps if the task genuinely requires distinct sequential phases.\n"
            "Review your PAST EXPERIENCES to avoid repeating historical mistakes or failed approaches.\n"
            "Return a valid JSON array of strings wrapped inside a strict <tasks_json>...</tasks_json> tag wrapper.\n\n"
            f"PAST EXPERIENCES:\n{past_experiences}\n\n"
            f"OBJECTIVE: {objective}"
        )
        try:
            model_name = (
                get_dna_config()
                .get("models", {})
                .get("fast", "gemini/gemini-2.5-flash")
            )
            # ⚡ OPTIMIZATION: Non-blocking call protects multi-agent loops from hanging
            response = await acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                api_key=vault.get_api_key_for_model(model_name),
            )
            raw_text = response.choices[0].message.content.strip()

            # ⚡ METABOLIC FIX: Track and account for tokens burned during decomposition
            step_tokens = (
                response.usage.get("total_tokens", 0)
                if hasattr(response, "usage")
                else 0
            )
            if step_tokens > 0:
                await asyncio.to_thread(log_metabolism, step_tokens)

            # Robust XML extraction layer
            xml_match = re.search(
                r"<tasks_json>(.*?)</tasks_json>", raw_text, re.DOTALL
            )
            clean_str = xml_match.group(1).strip() if xml_match else raw_text

            fence = chr(96) * 3
            if f"{fence}json" in clean_str:
                clean_str = clean_str.replace(f"{fence}json", "")
            if fence in clean_str:
                clean_str = clean_str.replace(fence, "")

            # ⚡ OPTIMIZATION: Call the isolated text parsing utility to enforce single-responsibility principles
            clean_str = self._clean_json_payload(raw_text)

            tasks = json.loads(clean_str)

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

        past_experiences = recall_recent_episodes()
        tasks = await self.decompose_goal(objective, past_experiences)
        console.print(
            f"[bold cyan]🧠 PFC: Objective split into {len(tasks)} executive pulses.[/bold cyan]"
        )

        final_outcome = "Success"
        for i, pulse_desc in enumerate(tasks):
            console.print(
                f"\n[bold yellow]🧠 PFC Executive Pulse {i + 1}/{len(tasks)}[/bold yellow]"
            )
            context = self.get_working_memory_context()
            augmented_prompt = f"GOAL: {objective}\nDOMAIN/ROUTE PREFERENCE: {domain} / {route}\nWORKING MEMORY:\n{context}\n\nCURRENT TASK: {pulse_desc}"
            try:
                await dispatch_task(augmented_prompt)
                self._remember(f"Pulse {i + 1} Executed: {pulse_desc}")
            except Exception as e:
                mocker_msg = (
                    f"[bold red]❌ Swarm Failure on Step {i + 1}: {str(e)}[/bold red]"
                )
                console.print(mocker_msg)
                final_outcome = f"Failed on Step {i + 1}: {str(e)}"
                break

        encode_episode(objective, tasks, final_outcome)
        return f"Consolidated {len(tasks)} pulses. Final state: {final_outcome}"
