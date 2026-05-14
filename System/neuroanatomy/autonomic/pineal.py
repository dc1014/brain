import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
LOG_FILE = ROOT_DIR / "logs" / "agent_interactions.jsonl"


def is_host_asleep(idle_hours_threshold: float = 4.0) -> bool:
    """
    The Pineal Gland monitors the interaction logs.
    If the human hasn't sent a command in X hours, it releases Melatonin.
    """
    if not LOG_FILE.exists():
        return True  # No activity at all, safe to dream

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return True

            last_line = lines[-1]
            data = json.loads(last_line)
            last_time_str = data.get("timestamp")

            if not last_time_str:
                return True

            last_time = datetime.fromisoformat(last_time_str)
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
    When the Pineal gland detects sleep, it first flushes the brain (Lymphatic),
    and then triggers REM sleep (DMN Daydreams).
    """
    console.print(
        "\n[bold magenta]🌙 Brain OS is entering Deep Sleep...[/bold magenta]"
    )

    # 1. Glymphatic Flush (Clean the brain)
    try:
        from System.neuroanatomy.systemic.lymphatic import flush_waste

        flush_waste()
    except Exception as e:
        console.print(f"[dim red]Lymphatic flush failed during sleep: {e}[/dim red]")

    # 2. Default Mode Network (REM Sleep / Daydreaming)
    try:
        from System.neuroanatomy.autonomic.dmn import trigger_daydreams  # type: ignore

        trigger_daydreams()
    except (ImportError, AttributeError):
        console.print("[dim]DMN not fully online yet. Skipping REM sleep.[/dim]")

    console.print(
        "[bold magenta]☀️ Sleep Cycle Complete. System optimized and waiting for host.[/bold magenta]\n"
    )
