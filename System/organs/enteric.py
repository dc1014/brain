import json
import difflib
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent
GUT_MEMORY_FILE = ROOT_DIR / "System" / "config" / "gut_memory.json"


def _ensure_gut():
    """Initializes the Enteric memory bank."""
    GUT_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not GUT_MEMORY_FILE.exists():
        with open(GUT_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def get_gut_reaction(prompt: str) -> tuple | None:
    """
    Checks if the gut has a biological reflex for this prompt.
    Returns the routing tuple if a >90% semantic match is found.
    """
    _ensure_gut()
    with open(GUT_MEMORY_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)

    if not cache:
        return None

    # Use Python's built-in SequenceMatcher to find a >90% similarity match instantly
    matches = difflib.get_close_matches(prompt.lower(), cache.keys(), n=1, cutoff=0.90)

    if matches:
        match = matches[0]
        data = cache[match]
        console.print(
            f"[bold green]🦠 Enteric Reflex Triggered: Bypassing Dispatcher. Gut routing matches '{match}'.[/bold green]"
        )

        # Return the exact tuple structure expected by analyze_task, but with 0 token usage
        return (
            data["is_valid"],
            data["reason"],
            data["route_type"],
            data["domain"],
            {"total_tokens": 0},
        )

    return None


def save_gut_reaction(
    prompt: str, is_valid: bool, reason: str, route_type: str, domain: str
) -> None:
    """Saves a Prefrontal Cortex routing decision into the gut for future reflexes."""
    _ensure_gut()
    with open(GUT_MEMORY_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)

    # Cache the routing logic
    cache[prompt.lower()] = {
        "is_valid": is_valid,
        "reason": reason,
        "route_type": route_type,
        "domain": domain,
    }

    with open(GUT_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
