from System.core.paths import ROOT_DIR
import json
import re
from rich.console import Console

console = Console()

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


def trigger_cerebellum_reflex(prompt: str) -> tuple | None:
    """
    The Gut-Brain Axis: Intercepts natural language prompts that map directly
    to known Cerebellar engrams, bypassing the Prefrontal Cortex entirely.
    """
    engram_dir = ROOT_DIR / "Meta" / "Engrams"
    if not engram_dir.exists():
        return None

    prompt_lower = prompt.lower()

    for f in engram_dir.glob("*.json"):
        engram_name = f.stem
        engram_name_spaced = engram_name.replace("_", " ")

        # Heuristic: If the prompt explicitly mentions the engram by name or spaced name
        if engram_name in prompt_lower or engram_name_spaced in prompt_lower:
            # Extract target directory heuristic
            path_match = re.search(
                r"(Studio|Personal|Professional|Media)/[\w-]+", prompt, re.IGNORECASE
            )
            target_dir = path_match.group(0) if path_match else "Studio"

            console.print(
                "\n[bold green]🦠 Enteric Nervous System Intercepted Prompt![/bold green]"
            )
            console.print(
                f"[dim]Gut mapped the intent to the '{engram_name}' muscle memory.[/dim]"
            )

            from System.tools import execute_engram

            res = execute_engram(engram_name, target_dir)

            if res.success:
                # ⚡ SHIFT-LEFT: Return False for 'is_valid' to cleanly abort the LLM Dispatcher
                # pipeline, but pass the execution success message back up to the user!
                return (
                    False,
                    f"ENTERIC REFLEX SUCCESS: {res.output}",
                    "NONE",
                    "NONE",
                    {"total_tokens": 0},
                )
            else:
                console.print(
                    "[bold red]Enteric Reflex failed. Falling back to Prefrontal Cortex...[/bold red]"
                )
                return None

    return None


def get_gut_reaction(prompt: str) -> tuple | None:
    """
    Checks if the gut has a biological reflex for this prompt.
    Returns the routing tuple if a match is found.
    """
    # 1. ⚡ Check for Muscle Memory (Engram) Interception First
    reflex_tuple = trigger_cerebellum_reflex(prompt)
    if reflex_tuple:
        return reflex_tuple

    # 2. Standard Enteric Routing Cache
    _ensure_gut()
    with open(GUT_MEMORY_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)

    if not cache:
        return None

    normalized_prompt = prompt.strip().lower()

    if normalized_prompt in cache:
        data = cache[normalized_prompt]

        if data["route_type"] in FORBIDDEN_CACHE_ROUTES:
            console.print(
                f"[dim yellow]🧠 Enteric Bypass: Route '{data['route_type']}' is too dangerous to cache. Forcing active LLM cognition.[/dim yellow]"
            )
            return None

        console.print(
            "[bold green]🦠 Enteric Reflex Triggered: Bypassing Dispatcher. Gut routing exact match found.[/bold green]"
        )

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

    if is_valid and route_type not in FORBIDDEN_CACHE_ROUTES:
        cache[prompt.strip().lower()] = {
            "is_valid": is_valid,
            "reason": reason,
            "route_type": route_type,
            "domain": domain,
        }
        with open(GUT_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
