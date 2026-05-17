import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent
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
