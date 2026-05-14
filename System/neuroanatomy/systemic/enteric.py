import json
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
GUT_MEMORY_FILE = ROOT_DIR / "System" / "config" / "gut_memory.json"

# SHIFT-LEFT SECURITY: Routes that are too dangerous to cache based on semantic similarity
FORBIDDEN_CACHE_ROUTES = [
    "FORGE",
    "SWARM",
    "EXECUTE",
    "SUBCONSCIOUS_FORAGE",
    "SUBCONSCIOUS_DAYDREAM",
]


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

    # SHIFT-LEFT: Exact O(1) Hash Matching.
    # We reject heuristics. If it's not a byte-for-byte identical request, we do not cache.
    normalized_prompt = prompt.strip().lower()

    if normalized_prompt in cache:
        data = cache[normalized_prompt]

        # 🛡️ THE PATCH: Invalidate cache for mutating/execution routes
        if data["route_type"] in FORBIDDEN_CACHE_ROUTES:
            console.print(
                f"[dim yellow]🧠 Enteric Bypass: Route '{data['route_type']}' is too dangerous to cache. Forcing active LLM cognition.[/dim yellow]"
            )
            return None

        console.print(
            "[bold green]🦠 Enteric Reflex Triggered: Bypassing Dispatcher. Gut routing exact match found.[/bold green]"
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

    # We only cache successful, safe routing decisions
    if is_valid and route_type not in FORBIDDEN_CACHE_ROUTES:
        cache[prompt.strip().lower()] = {
            "is_valid": is_valid,
            "reason": reason,
            "route_type": route_type,
            "domain": domain,
        }
        with open(GUT_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
