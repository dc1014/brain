# --- System/neuroanatomy/autonomic/interoception.py ---
import json
import yaml
from datetime import datetime
from System.core.paths import ROOT_DIR

LOG_DIR = ROOT_DIR / "logs"
METABOLISM_FILE = LOG_DIR / "metabolism.json"
SYSTEM_CONFIG_PATH = ROOT_DIR / "System" / "config" / "system.yaml"


def get_token_budget() -> int:
    """Reads the maximum daily token budget from system.yaml, defaulting to 500,000."""
    default_limit = 500_000
    if not SYSTEM_CONFIG_PATH.exists():
        return default_limit
    try:
        with open(SYSTEM_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("max_daily_token_budget", default_limit)
    except Exception:
        return default_limit


def get_current_metabolism() -> dict:
    """Reads the current energy levels. Automatically resets on a new day (Sleep)."""
    today = datetime.now().strftime("%Y-%m-%d")
    default_state = {"date": today, "tokens_burned": 0, "exhausted": False}

    if not METABOLISM_FILE.exists():
        return default_state

    try:
        with open(METABOLISM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # If it's a new day, the system woke up fresh. Reset the metabolism.
        if data.get("date") != today:
            return default_state
        return data
    except Exception:
        return default_state


def log_metabolism(tokens: int) -> None:
    """Burns calories (tokens) and updates the internal state."""
    if tokens <= 0:
        return

    data = get_current_metabolism()
    data["tokens_burned"] += tokens

    limit = get_token_budget()
    if data["tokens_burned"] >= limit:
        data["exhausted"] = True
    else:
        data["exhausted"] = False

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(METABOLISM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def validate_metabolic_clearance() -> tuple[bool, str]:
    """
    Checks if the system has sufficient daily token budget remaining to execute a task.
    Returns (True, message) if clear, or (False, error_message) if exhausted.
    """
    data = get_current_metabolism()
    limit = get_token_budget()

    if data["tokens_burned"] >= limit:
        return (
            False,
            f"Metabolic budget exhausted for today ({data['tokens_burned']:,}/{limit:,} tokens used).",
        )

    return True, "Clearance approved."
