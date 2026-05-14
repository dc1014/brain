from System.core.paths import ROOT_DIR
import json
from datetime import datetime


LOG_DIR = ROOT_DIR / "logs"
METABOLISM_FILE = LOG_DIR / "metabolism.json"

# Daily token limit before the system enters "Exhaustion"
DAILY_TOKEN_LIMIT = 500_000


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

    if data["tokens_burned"] >= DAILY_TOKEN_LIMIT:
        data["exhausted"] = True

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(METABOLISM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def check_energy_levels() -> tuple[bool, int]:
    """Returns (is_exhausted, tokens_burned)"""
    data = get_current_metabolism()
    return data.get("exhausted", False), data.get("tokens_burned", 0)
