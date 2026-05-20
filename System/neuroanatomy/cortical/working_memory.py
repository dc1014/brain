from rich.console import Console
from litellm import acompletion  # type: ignore
from System.core.dna import get_dna_config
from System.neuroanatomy.systemic.immune_system import vault

console = Console()


class WorkingMemory:
    """PFC Working Memory (Semantic Compressor)."""

    def __init__(self, core_objective: str) -> None:
        self.core_objective = core_objective
        self.established_facts: list[str] = []
        self.recent_activity: list[str] = []
        self.compression_threshold_chars = 12000

    def add_event(self, agent_name: str, raw_output: str, actions: list[str]) -> None:
        # Wrap events in clean, structured semantic tags for Gemini context attention
        event_log = (
            f'<activity_node agent="{agent_name}">\n'
            f"<raw_telemetry>\n{raw_output}\n</raw_telemetry>\n"
            f"<actions_taken>{actions}</actions_taken>\n"
            f"</activity_node>"
        )
        self.recent_activity.append(event_log)

    def get_current_context(self) -> str:
        context = f"CORE OBJECTIVE: {self.core_objective}\n\n"
        if self.established_facts:
            context += "<established_facts>\n"
            for fact in self.established_facts:
                context += f"- {fact}\n"
            context += "</established_facts>\n\n"
        if self.recent_activity:
            context += "<recent_pipeline_activity>\n"
            context += "\n\n".join(self.recent_activity)
            context += "\n</recent_pipeline_activity>"
        return context

    async def compress_if_bloated(self) -> None:
        current_text = "\n".join(self.recent_activity)
        if len(current_text) < self.compression_threshold_chars:
            return

        console.print(
            "[dim magenta]🧠 PFC Buffer Full: Compressing working memory...[/dim magenta]"
        )
        prompt = (
            "You are the Prefrontal Cortex. Synthesize the following pipeline activity into a highly "
            "concise, bulleted list of 'Established Facts' and 'Current State' wrapped in <summary_update> tags.\n"
            "Discard all conversational filler and preserve ONLY technical facts, code paths, and outcomes.\n\n"
            f"ACTIVITY LOG:\n{current_text}"
        )
        try:
            model = (
                get_dna_config()
                .get("models", {})
                .get("fast", "gemini/gemini-2.5-flash")
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
