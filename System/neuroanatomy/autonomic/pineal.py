from System.core.paths import ROOT_DIR
import json
from datetime import datetime, timezone, timedelta
from rich.console import Console

console = Console()

LOG_FILE = ROOT_DIR / "logs" / "agent_interactions.jsonl"


def is_host_asleep(idle_hours_threshold: float = 4.0) -> bool:
    """
    The Pineal Gland monitors the interaction logs.
    It reads backwards through the log to find the last time the "HUMAN" origin initiated a task.
    If the human hasn't sent a command in X hours, it releases Melatonin.
    """
    if not LOG_FILE.exists():
        return True  # No activity at all, safe to dream

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return True

            # ⚡ THE FIX: Read backwards to find the last explicit human interaction
            last_human_time_str = None
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    # Legacy logs without an origin are assumed to be HUMAN
                    if data.get("origin", "HUMAN") == "HUMAN":
                        last_human_time_str = data.get("timestamp")
                        break
                except json.JSONDecodeError:
                    continue

            if not last_human_time_str:
                return True

            last_time = datetime.fromisoformat(last_human_time_str)
            time_since_last_action = datetime.now(timezone.utc) - last_time

            if time_since_last_action > timedelta(hours=idle_hours_threshold):
                console.print(
                    f"[dim blue]🌙 Pineal Gland: Host has been idle for {time_since_last_action.seconds // 3600} hours. Releasing Melatonin.[/dim blue]"
                )
                return True

    except Exception as e:
        console.print(f"[dim red]Pineal Gland error: {e}[/dim red]")

    return False


def enter_sleep_cycle() -> None:
    """
    The Circadian Rhythm trigger.
    When the Pineal gland detects sleep, it consolidates memory, flushes waste, and triggers REM sleep.
    """
    console.print(
        "\n[bold magenta]🌙 Brain OS is entering Deep Sleep...[/bold magenta]"
    )

    # 0. Hippocampus Consolidation
    try:
        from System.neuroanatomy.limbic.hippocampus import consolidate_short_term_memory

        consolidate_short_term_memory()
    except Exception as e:
        console.print(f"[dim red]Hippocampus consolidation failed: {e}[/dim red]")

    # 1. Glymphatic Flush
    try:
        from System.neuroanatomy.systemic.lymphatic import flush_waste

        flush_waste(max_log_lines=0)
    except Exception as e:
        console.print(f"[dim red]Lymphatic flush failed during sleep: {e}[/dim red]")

    # 2. Default Mode Network (REM Sleep)
    try:
        from System.neuroanatomy.autonomic.dmn import trigger_daydreams

        trigger_daydreams()
    except Exception as e:
        console.print(f"[dim red]DMN failed to trigger daydreams: {e}[/dim red]")

    console.print(
        "[bold yellow]☀️ Sleep Cycle Complete. System optimized and waiting for host.[/bold yellow]"
    )
