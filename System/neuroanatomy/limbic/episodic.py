import json
import time
from rich.console import Console
from System.core.paths import ROOT_DIR
from System.core.locks import BiologicalLock
from System.neuroanatomy.limbic.nucleus_accumbens import process_dopaminergic_reward

console = Console()
MEMORY_FILE = ROOT_DIR / "Meta" / "autobiography.jsonl"


def encode_episode(objective: str, tasks: list[str], outcome: str) -> None:
    """Hippocampal Encoding: Saves a permanent memory of an enacted executive sequence."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    episode = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "objective": objective,
        "tasks_executed": tasks,
        "outcome": outcome,
    }

    with BiologicalLock(str(MEMORY_FILE)):
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(episode) + "\n")

    # ⚡ SHIFT-LEFT: Immediately pass the outcome to the Nucleus Accumbens for behavioral adjustment
    process_dopaminergic_reward(objective, outcome)


def recall_recent_episodes(limit: int = 5) -> str:
    """Retrieves recent autobiographical memory to provide context and prevent repeated mistakes."""
    if not MEMORY_FILE.exists():
        return "No previous life experiences recorded."

    episodes = []
    with BiologicalLock(str(MEMORY_FILE)):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    episodes.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not episodes:
        return "No previous life experiences recorded."

    recent = episodes[-limit:]
    formatted_memories = []

    for ep in recent:
        formatted_memories.append(
            f"[{ep['timestamp']}] GOAL: {ep['objective']} | "
            f"OUTCOME: {ep['outcome']} | STEPS: {', '.join(ep['tasks_executed'])}"
        )

    return "\n".join(formatted_memories)
