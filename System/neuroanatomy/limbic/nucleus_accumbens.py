import json
from rich.console import Console
from litellm import completion  # type: ignore

from System.core.paths import ROOT_DIR
from System.core.locks import BiologicalLock
from System.core.dna import AGENT_CONFIG

console = Console()
PLASTICITY_FILE = ROOT_DIR / "Meta" / "plasticity_weights.json"


def get_plasticity_rules() -> str:
    """Retrieves all dynamically learned rules to be injected into the LLM's base consciousness."""
    if not PLASTICITY_FILE.exists():
        return ""

    with BiologicalLock(str(PLASTICITY_FILE)):
        try:
            with open(PLASTICITY_FILE, "r", encoding="utf-8") as f:
                rules = json.load(f)
                if not rules:
                    return ""
                return "\n".join(f"- {rule}" for rule in rules)
        except json.JSONDecodeError:
            return ""


def process_dopaminergic_reward(objective: str, outcome: str) -> None:
    """
    The Nucleus Accumbens: Evaluates an episodic outcome.
    If the outcome was a failure, it generates a permanent behavioral rule
    to prevent the organism from ever making the same mistake again.
    """
    if "Success" in outcome or "Success" == outcome.strip():
        # Goal succeeded: Dopamine release (Pathways reinforced implicitly by Episodic Memory)
        return

    # Goal failed: Cortisol release (Trigger Long-Term Potentiation to alter future behavior)
    console.print(
        "[bold magenta]🧬 Nucleus Accumbens: Pain detected. Triggering Synaptic Plasticity...[/bold magenta]"
    )

    prompt = (
        "You are the Nucleus Accumbens of Brain OS. The organism just experienced a failure.\n"
        f"OBJECTIVE: {objective}\n"
        f"FAILURE OUTCOME: {outcome}\n\n"
        "Based on this pain, write a SINGLE, concise, imperative rule that must be added to "
        "the agent's core system prompt to ensure this specific mistake never happens again. "
        "Return ONLY the rule string, nothing else."
    )

    try:
        model_name = AGENT_CONFIG.get("models", {}).get(
            "fast", "gemini/gemini-2.5-flash"
        )
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        learned_rule = response.choices[0].message.content.strip()

        # Clean up quotes if the LLM wraps it
        if learned_rule.startswith('"') and learned_rule.endswith('"'):
            learned_rule = learned_rule[1:-1]

        console.print(f"[dim magenta]LTP Rule Formed: '{learned_rule}'[/dim magenta]")

        # Physically alter the brain's long-term behavioral weights
        PLASTICITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        rules = []

        with BiologicalLock(str(PLASTICITY_FILE)):
            if PLASTICITY_FILE.exists():
                try:
                    with open(PLASTICITY_FILE, "r", encoding="utf-8") as f:
                        rules = json.load(f)
                except json.JSONDecodeError:
                    rules = []

            if learned_rule not in rules:
                rules.append(learned_rule)
                # Keep only the 20 most recent core beliefs to prevent prompt bloat
                if len(rules) > 20:
                    rules.pop(0)

                with open(PLASTICITY_FILE, "w", encoding="utf-8") as f:
                    json.dump(rules, f, indent=2)

    except Exception as e:
        console.print(
            f"[dim red]Neuroplasticity failure (Reward pathway bypassed): {str(e)}[/dim red]"
        )
