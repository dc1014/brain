import json
import re
from typing import Any

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

        # ⚡ UNIX PHILOSOPHY: Centralize canonical string layout compaction inside the memory subsystem
        context = re.sub(r"\n{3,}", "\n\n", context)
        context = re.sub(r"[ \t]{2,}", " ", context)
        return context.strip()

    async def compress_if_bloated(self) -> None:
        raw_text = "\n".join(self.recent_activity)
        if len(raw_text) < self.compression_threshold_chars:
            return

        # ⚡ STRUCTURAL FIX: Deduplicate repetitive text lines while preserving independent XML nodes
        seen_lines = set()
        optimized_activity = []

        for event in self.recent_activity:
            event_lines = []
            for line in event.splitlines():
                trimmed = line.strip()
                if trimmed and len(trimmed) > 50 and trimmed in seen_lines:
                    continue
                # Shield structural system XML boundaries from being accidentally ingested by the duplicate tracker
                if (
                    trimmed
                    and len(trimmed) > 50
                    and not trimmed.startswith(
                        (
                            "<activity_node",
                            "</activity_node",
                            "<raw_telemetry",
                            "</raw_telemetry",
                        )
                    )
                ):
                    seen_lines.add(trimmed)
                event_lines.append(line)
            optimized_activity.append("\n".join(event_lines))

        current_text = "\n".join(optimized_activity)

        # Check if the algorithmic pass successfully cleared space without invoking cloud resources
        if len(current_text) < self.compression_threshold_chars:
            self.recent_activity = optimized_activity
            console.print(
                "[dim green]⚡ Token Optimization: Algorithmic pruning cleared memory bloat while preserving XML nodes.[/dim green]"
            )
            return

        console.print(
            "[dim magenta]🧠 PFC Buffer Full: Compressing working memory via fallback summary model...[/dim magenta]"
        )
        # 🛡️ SHIFT-LEFT SECURITY: Scrub secrets from internal cognitive loops before background LLM dispatch
        safe_current_text = vault.mask_secrets(current_text)

        prompt = (
            "You are the Prefrontal Cortex. Synthesize the following pipeline activity into a highly "
            "concise, bulleted list of 'Established Facts' and 'Current State' wrapped in <summary_update> tags.\n"
            "Discard all conversational filler and preserve ONLY technical facts, code paths, and outcomes.\n\n"
            f"ACTIVITY LOG:\n{safe_current_text}"
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


async def compress_message_array(
    messages: list[dict[str, Any]], current_model: str
) -> list[dict[str, Any]]:
    """
    Evaluates the token footprint of the message array. If it approaches context limits,
    spawns a fast background model to compress the historical middle into a dense Working Memory block.
    """
    try:
        # ⚡ ZERO-DEBT FIXED: Reconstruct array via shallow copies to eliminate in-place mutation side-effects
        optimized_messages = []
        for msg in messages:
            msg_copy = dict(msg)
            content = msg_copy.get("content", "")
            if isinstance(content, str) and len(content) > 4000:
                lines = content.splitlines()
                if len(lines) > 60:
                    msg_copy["content"] = (
                        "\n".join(lines[:20])
                        + f"\n\n--- [ALGORITHMIC CONTEXT FILTER: Sliced {len(lines) - 40} lines of structural noise] ---\n\n"
                        + "\n".join(lines[-20:])
                    )
            optimized_messages.append(msg_copy)

        text_content = json.dumps(optimized_messages, default=str)
        if len(text_content) < 12000 and len(messages) <= 6:
            # ⚡ FIXED: Return the optimized messages array to preserve individual payload slicing passes
            return optimized_messages

        console.print(
            "[dim magenta]🧠 Context Window Bloated: Compressing historical messages...[/dim magenta]"
        )

        head = optimized_messages[:2]
        tail = optimized_messages[-2:]
        middle = optimized_messages[2:-2]

        if not middle:
            return messages

        # Extract previous working memory from the User prompt so the compressor can carry it forward
        user_content = head[1].get("content", "")
        old_summary = ""
        if "--- COMPRESSED WORKING MEMORY ---" in user_content:
            parts = user_content.split("--- COMPRESSED WORKING MEMORY ---")
            user_content = parts[0].strip()
            old_summary = parts[1].strip()

        # Format the history
        history_text = ""
        if old_summary:
            history_text += f"[PREVIOUS WORKING MEMORY]: {old_summary}\n\n"

        for m in middle:
            role = m.get("role", "unknown")
            content = m.get("content", "")
            if isinstance(content, str):
                history_text += f"[{role.upper()}]: {content}\n\n"
            else:
                history_text += f"[{role.upper()}]: {json.dumps(content)}\n\n"

        # 🛡️ SHIFT-LEFT SECURITY: Scrub secrets from conversation history before background LLM dispatch
        safe_history_text = vault.mask_secrets(history_text)

        prompt = (
            "You are the Prefrontal Cortex Context Compressor.\n"
            "Summarize the following historical conversation and tool executions into a highly dense, "
            "bulleted 'Working Memory' block. Retain all factual data, discovered file paths, code snippets, and tool outcomes. "
            "Discard all conversational filler and JSON formatting.\n\n"
            f"HISTORY TO COMPRESS:\n{safe_history_text}"
        )

        fast_model = (
            get_dna_config().get("models", {}).get("fast", "gemini/gemini-2.5-flash")
        )

        # Spawn the background compression pulse
        response = await acompletion(
            model=fast_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            api_key=vault.get_api_key_for_model(fast_model),
        )

        summary = response.choices[0].message.content.strip()

        # Inject the new compressed memory directly into the original User prompt
        new_user_content = (
            user_content + f"\n\n--- COMPRESSED WORKING MEMORY ---\n{summary}"
        )
        new_head = [head[0], {"role": "user", "content": new_user_content}]

        console.print(
            "[dim green]✅ Historical context successfully compressed into Working Memory.[/dim green]"
        )

        return new_head + tail

    except Exception as e:
        console.print(
            f"[dim red]Context Compression Failed: {e}. Falling back to FIFO amnesia.[/dim red]"
        )
        window = messages[-5:]
        while window and window[0].get("role") == "tool":
            window.pop(0)
        return [messages[0], messages[1]] + window
