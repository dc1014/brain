import os
import time
import asyncio
from pathlib import Path
from typing import Optional
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.neuroanatomy.cortical.executive_loop import execute_pipeline
from System.neuroanatomy.limbic.hippocampus import recall_memory

console = Console()


def _gather_dream_context(daydream_file: Path, topic: Optional[str] = None) -> str:
    """Gathers recent short-term logs, past hypotheses, and local memory via zero-token search."""
    context_pieces = []

    # ⚡ ZERO-TOKEN KNOWLEDGE RETRIEVAL: If a topic is provided, search the local FTS5 SQLite index
    # before spending API tokens. This gives the DMN agent massive context for free.
    if topic:
        console.print(
            f"[dim cyan]🧠 Hippocampus: Retrieving zero-token local memories for '{topic}'...[/dim cyan]"
        )
        try:
            topic_memories = recall_memory(topic, limit=5)
            if topic_memories and "No memories found" not in topic_memories:
                context_pieces.append(
                    f"--- RELEVANT LOCAL KNOWLEDGE FOR '{topic.upper()}' ---\n{topic_memories}"
                )
        except Exception as e:
            console.print(f"[dim red]Hippocampus recall degraded: {e}[/dim red]")

    # Append standard background life-support logs
    log_file = ROOT_DIR / "System" / "logs" / "experiment_log.md"
    if log_file.exists():
        try:
            log_text = log_file.read_text(encoding="utf-8").strip()
            if log_text:
                context_pieces.append(
                    f"--- RECENT WAKING TELEMETRY LOGS ---\n{log_text[-3000:]}"
                )
        except Exception:
            pass

    medulla_log = ROOT_DIR / "System" / "logs" / "medulla.log"
    if medulla_log.exists():
        try:
            medulla_text = medulla_log.read_text(encoding="utf-8").strip()
            if medulla_text:
                context_pieces.append(
                    f"--- RECENT MEDULLA DAEMON LOGS ---\n{medulla_text[-3000:]}"
                )
        except Exception:
            pass

    if daydream_file.exists():
        try:
            history_text = daydream_file.read_text(encoding="utf-8").strip()
            if history_text:
                context_pieces.append(
                    f"--- HISTORICAL STRATEGIC HYPOTHESES ---\n{history_text[-3000:]}"
                )
        except Exception:
            pass

    if not context_pieces:
        agents_config = ROOT_DIR / "System" / "config" / "agents.yaml"
        if agents_config.exists():
            try:
                context_pieces.append(
                    f"--- CORE SYSTEM CONFIGURATIONS FOR REFLECTION ---\n{agents_config.read_text(encoding='utf-8')[:4000]}"
                )
            except Exception:
                pass

    return "\n\n".join(context_pieces)


def trigger_daydreams(topic: Optional[str] = None, domain: Optional[str] = None) -> str:
    """The Hardened Default Mode Network (DMN). Synthesizes strategic insights via secure agent routing."""
    # ⚡ DEFAULT SCOPE RESTORATION: Default clean runs globally to NONE instead of STUDIO
    target_domain_raw = (
        domain if domain is not None else os.environ.get("BRAIN_OS_DOMAIN", "NONE")
    )
    assigned_domain = str(target_domain_raw).upper()

    target_workspace = ROOT_DIR / "Meta" / "DMN"
    daydream_file = target_workspace / "daydreams.md"
    daydream_file.parent.mkdir(parents=True, exist_ok=True)

    # Ingest short-term logs safely using clean Python file streams, passing the topic
    dream_context = _gather_dream_context(daydream_file, topic=topic)
    if not dream_context.strip() and not topic:
        return "No neurological context available to daydream."

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if topic:
        console.print(
            f"\n[bold magenta]🌌 DMN ACTIVE:[/bold magenta] Directing focus onto topic: [underline]{topic}[/underline] inside [bold]{assigned_domain}[/bold]"
        )
        input_payload = (
            f"Current Timestamp: {timestamp}\n"
            f"Assigned Execution Domain Subsystem: {assigned_domain}\n"
            f"Topic Target: {topic}\n\n"
            f"BACKGROUND DATA CONTEXT:\n{dream_context}\n\n"
            f"INSTRUCTION: Thoroughly analyze the context regarding '{topic}'. Synthesize your strategic insights, "
            f"format them cleanly under a '## 🌌 Epiphany ({timestamp})' markdown header line block, and immediately "
            f"call your `append_safe_file` tool to append your finished report content into the file path: 'Meta/DMN/daydreams.md'."
        )
    else:
        console.print(
            f"\n[bold magenta]🌌 DMN ACTIVE:[/bold magenta] Synthesizing trends for domain: [bold]{assigned_domain}[/bold]"
        )
        input_payload = (
            f"Current Timestamp: {timestamp}\n"
            f"Assigned Execution Domain Subsystem: {assigned_domain}\n\n"
            f"BACKGROUND DATA CONTEXT:\n{dream_context}\n\n"
            f"INSTRUCTION: Scan recent logs for anomalies, state-machine trends, or refactoring loops. Synthesize your strategic insights, "
            f"format them cleanly under a '## 🌌 Epiphany ({timestamp})' markdown header line block, and immediately "
            f"call your `append_safe_file` tool to append your finished report content into the file path: 'Meta/DMN/daydreams.md'."
        )

    try:
        console.print(
            "[dim magenta]🧠 DMN: Awakening 'The Daydreamer (DMN)' agent within secure pipeline...[/dim magenta]"
        )

        # Fire execution. The orchestrator handles displaying layout mirrors natively to your terminal screen.
        asyncio.run(
            execute_pipeline(
                input_payload,
                "SUBCONSCIOUS_DAYDREAM",
                assigned_domain,
                origin="AUTONOMIC",
            )
        )

        # Settle file system hooks
        time.sleep(0.5)

    except Exception as e:
        console.print(f"[bold red]❌ DMN Execution Failure: {str(e)}[/bold red]")
        return f"Failure: {str(e)}"

    # ⚡ UNCONDITIONAL LEDGER LINK: Projects your clickable path reference safely at the conclusion of the track
    absolute_clickable_link = f"file:///{str(daydream_file).replace('\\', '/')}"
    return (
        f"Centralized Default Mode Network sequence complete.\n"
        f"🔗 [bold cyan]Ledger updated natively at:[/bold cyan] Meta/DMN/daydreams.md\n"
        f"🔗 [bold cyan]Clickable Local File URL Link:[/bold cyan] [underline]{absolute_clickable_link}[/underline]"
    )
