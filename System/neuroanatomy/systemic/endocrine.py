import json
import time
from typing import Any
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.core.locks import BiologicalLock

console = Console()
ENDOCRINE_FILE = ROOT_DIR / "Meta" / "humoral_state.json"


class EndocrineSystem:
    """
    Diffuse Neuromodulation (The Bloodstream).
    Maintains a continuous, multi-dimensional floating-point vector representing
    the system's chemical state, which dynamically biases all LLM computations.
    """

    def __init__(self) -> None:
        ENDOCRINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_bloodstream()

    def _initialize_bloodstream(self) -> None:
        """Sets baseline homeostasis if no state exists."""
        if not ENDOCRINE_FILE.exists():
            base_state = {
                "cortisol": 0.0,  # Stress / Scarcity
                "dopamine": 0.5,  # Reward / Exploration
                "adrenaline": 0.0,  # Crisis / Urgency
                "melatonin": 0.0,  # Fatigue
                "last_updated": time.time(),
            }
            self._write_state(base_state)

    def _read_state(self) -> dict[str, Any]:
        try:
            with BiologicalLock(str(ENDOCRINE_FILE)):
                with open(ENDOCRINE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return {
                "cortisol": 0.0,
                "dopamine": 0.5,
                "adrenaline": 0.0,
                "melatonin": 0.0,
            }

    def _write_state(self, state: dict[str, Any]) -> None:
        state["last_updated"] = time.time()
        # Clamp all values between 0.0 and 1.0 to respect biological limits
        for key in ["cortisol", "dopamine", "adrenaline", "melatonin"]:
            if key in state:
                state[key] = max(0.0, min(1.0, float(state[key])))

        with BiologicalLock(str(ENDOCRINE_FILE)):
            with open(ENDOCRINE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)

    def secrete(self, hormone: str, amount: float) -> None:
        """Releases a hormone into the bloodstream, spiking its current levels."""
        state = self._read_state()
        if hormone in state:
            state[hormone] += amount
            self._write_state(state)
            console.print(
                f"[dim magenta]🩸 Endocrine: {hormone.capitalize()} spike (+{amount}).[/dim magenta]"
            )

    def metabolize(self) -> None:
        """Decays all active hormones slowly back toward 0.0 (Homeostasis)."""
        state = self._read_state()
        decay_rate = 0.05

        for key in ["cortisol", "adrenaline", "melatonin"]:
            state[key] = max(0.0, state[key] - decay_rate)

        # Dopamine idles around 0.3 for baseline motivation
        if state["dopamine"] > 0.3:
            state["dopamine"] -= decay_rate
        elif state["dopamine"] < 0.3:
            state["dopamine"] += decay_rate

        self._write_state(state)

    def get_humoral_vector(self) -> dict[str, float]:
        """Returns the current neuromodulation vector."""
        state = self._read_state()
        return {k: float(v) for k, v in state.items() if k != "last_updated"}


def is_cortisol_active() -> bool:
    """Legacy reflex check: Returns True if Cortisol is critically high."""
    try:
        endocrine = EndocrineSystem()
        return endocrine.get_humoral_vector()["cortisol"] > 0.7
    except Exception:
        return False
