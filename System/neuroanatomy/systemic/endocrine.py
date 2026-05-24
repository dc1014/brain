import json
import time
from typing import Any
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.core.locks import StateLock
from System.core.dna import get_dna_config

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
            with StateLock(str(ENDOCRINE_FILE)):
                with open(ENDOCRINE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return {
                "cortisol": 0.0,
                "dopamine": 0.5,
                "adrenaline": 0.0,
                "melatonin": 0.0,
                "last_updated": time.time(),
            }

    def _write_state(self, state: dict[str, Any]) -> None:
        state["last_updated"] = time.time()
        # Clamp values between 0.0 and 1.0
        for k in ["cortisol", "dopamine", "adrenaline", "melatonin"]:
            if k in state:
                state[k] = max(0.0, min(1.0, float(state[k])))
        try:
            with StateLock(str(ENDOCRINE_FILE)):
                with open(ENDOCRINE_FILE, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2)
        except Exception as e:
            console.print(f"[bold red]Endocrine Error: {e}[/bold red]")

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

    def calculate_token_limit(self, model: str) -> int:
        """
        💸 COST & METABOLISM SHIELD:
        Calculates maximum token limits dynamically based on model pricing tiers
        and active chemical stress levels to preserve aggregator wallet balances.
        """
        model_lower = model.lower()
        state = self._read_state()

        # 1. Base allocations mapped via tier pricing signatures
        if any(exp in model_lower for exp in ["opus", "gpt-4", "sonnet", "pro"]):
            base_budget = 2000  # Hard restriction on expensive tiers
        else:
            base_budget = 4000  # Expanded budget for cost-efficient tiers

        # 2. Humoral Contraction Matrix (Adrenaline/Cortisol stress compression)
        stress = max(state.get("adrenaline", 0.0), state.get("cortisol", 0.0))
        if stress > 0.5:
            # Squeeze token execution space down up to 60% during emergency windows
            base_budget = int(base_budget * (1.0 - (stress * 0.6)))

        return max(500, base_budget)


def is_cortisol_active() -> bool:
    """Utility check for severe systemic exhaustion."""
    system = EndocrineSystem()
    vector = system.get_humoral_vector()
    return vector["cortisol"] > 0.7


def get_resolved_model(desired_model_key: str, is_exhausted: bool) -> str:
    """
    HUMORAL ROUTING: Resolves the fallback LLM models securely using the Vault.
    Downgrades to efficiency models if Cortisol (exhaustion) is active.
    """
    from System.neuroanatomy.systemic.immune_system import vault

    if is_exhausted:
        system = EndocrineSystem()
        system.secrete("cortisol", 0.5)

        if is_cortisol_active():
            desired_model_key = "gpt_mini"

    desired_model_str = get_dna_config().get("models", {}).get(desired_model_key, "")

    if vault.get_api_key_for_model(desired_model_str):
        return desired_model_str

    if vault.get_api_key_for_model("openai/gpt"):
        return get_dna_config().get("models", {}).get("gpt_mini", "openai/gpt-4o-mini")
    elif vault.get_api_key_for_model("anthropic/claude"):
        return (
            get_dna_config()
            .get("models", {})
            .get("claude_haiku", "anthropic/claude-haiku-4-5")
        )
    elif vault.get_api_key_for_model("gemini/"):
        return (
            get_dna_config()
            .get("models", {})
            .get("gemini_flash", "gemini/gemini-2.5-flash")
        )

    return desired_model_str
