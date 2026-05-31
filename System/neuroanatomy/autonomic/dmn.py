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

    # ⚡ ZERO-TOKEN KNOWLEDGE RETRIEVAL: Search the local FTS5 SQLite index before spending API tokens.
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
    """The Active Default Mode Network (DMN). Investigates active goals and queues proactive tasks."""
    target_domain_raw = (
        domain if domain is not None else os.environ.get("BRAIN_OS_DOMAIN", "NONE")
    )
    assigned_domain = str(target_domain_raw).upper()

    target_workspace = ROOT_DIR / "Meta" / "DMN"
    daydream_file = target_workspace / "daydreams.md"
    daydream_file.parent.mkdir(parents=True, exist_ok=True)

    # ⚡ PHASE 4: Dual-Memory Context Extraction
    beliefs_file = ROOT_DIR / "Meta" / "Core_Beliefs.md"
    core_beliefs = (
        beliefs_file.read_text(encoding="utf-8")
        if beliefs_file.exists()
        else "No Core Beliefs defined."
    )

    goals_file = ROOT_DIR / "Meta" / "Goals.md"
    active_goals = []
    if goals_file.exists():
        goal_lines = goals_file.read_text(encoding="utf-8").splitlines()
        for line in goal_lines:
            # Token Optimization: Extract ONLY headers and active/in-progress tasks
            stripped = line.lstrip()
            if (
                stripped.startswith("#")
                or stripped.startswith("- [ ]")
                or stripped.startswith("- [-]")
            ):
                active_goals.append(line)

    active_goals_context = (
        "\n".join(active_goals) if active_goals else "No active goals found."
    )

    dream_context = _gather_dream_context(daydream_file, topic=topic)
    if not dream_context.strip() and not topic:
        return "No neurological context available to daydream."

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    domain_prompts = {
        "STUDIO": "Focus on advancing active projects, writing code, drafting blueprints, and resolving technical or creative debt.",
        "PERSONAL": "Focus on creative synthesis, life organization, personal writing, and habit tracking.",
        "PROFESSIONAL": "Focus on career strategy, business operations, marketing vectors, and communication follow-ups.",
        "META": "Focus on CoreTex OS maintenance, log anomalies, file organization, and system optimization.",
    }
    domain_focus = domain_prompts.get(
        assigned_domain, "Focus on general optimization and goal advancement."
    )

    # ⚡ PHASE 5: Proactive Execution Queueing with Thread IDs
    queue_instructions = (
        f"PHASE 1 (INVESTIGATION): Actively use your tools (`read_safe_file`, `web_search`, `search_vault`) to gather context on the user's Active Subgoals. Read their project files or research external concepts.\n"
        f"PHASE 2 (SYNTHESIS): Synthesize your strategic insights under a '## 🌌 Epiphany ({timestamp})' header and append it to 'Meta/DMN/daydreams.md' using `append_safe_file`.\n"
        f"PHASE 3 (PROACTIVE EXECUTION): Decompose the current Active Subgoal into 1-2 highly specific, actionable CLI tasks. "
        f"Append them to 'Meta/Pending_Actions.md' using `append_safe_file` with EXACTLY this format:\n\n"
        f"### ⏳ Pending Task ({timestamp})\n"
        f"**Prompt:** [Your specific CLI/Agent task here]\n"
        f"**Thalamus Route:** `WORKSPACE` | **Domain:** `{assigned_domain}`\n"
        f"**Teleology Thread:** [Insert the exact #goal/UID tag from the Goals.md file]\n"
        f"> **Threat Analysis & Reasoning:** [Why this advances the subgoal]\n---\n"
    )

    console.print(
        f"\n[bold magenta]🌌 DMN ACTIVE:[/bold magenta] Synthesizing trends for domain: [bold]{assigned_domain}[/bold]"
    )
    input_payload = (
        f"Current Timestamp: {timestamp}\n"
        f"Assigned Execution Domain: {assigned_domain}\n"
        f"Domain Directive: {domain_focus}\n\n"
        f"USER CORE BELIEFS (WHO THEY ARE):\n{core_beliefs}\n\n"
        f"ACTIVE GOAL FRONTLINE (WHAT THEY ARE DOING):\n{active_goals_context}\n\n"
        f"BACKGROUND LOG CONTEXT:\n{dream_context}\n\n"
        f"INSTRUCTION: {queue_instructions}"
    )

    try:
        console.print(
            "[dim magenta]🧠 DMN: Awakening 'The Daydreamer' agent within secure pipeline...[/dim magenta]"
        )
        asyncio.run(
            execute_pipeline(
                input_payload,
                "SUBCONSCIOUS_DAYDREAM",
                assigned_domain,
                origin="AUTONOMIC",
            )
        )
        time.sleep(0.5)
    except Exception as e:
        console.print(f"[bold red]❌ DMN Execution Failure: {str(e)}[/bold red]")
        return f"Failure: {str(e)}"

    absolute_clickable_link = f"file:///{str(daydream_file).replace('\\', '/')}"
    return (
        f"Centralized Default Mode Network sequence complete.\n"
        f"🔗 [bold cyan]Ledger updated natively at:[/bold cyan] Meta/DMN/daydreams.md\n"
        f"🔗 [bold cyan]Clickable Local File URL Link:[/bold cyan] [underline]{absolute_clickable_link}[/underline]"
    )
