import threading
from typing import Any, Callable
from functools import wraps
from rich.console import Console

console = Console()


class Spine:
    """
    The Spine (Central Inbound Pathway).
    Routes raw sensory stimuli to Somatic Reflexes, Metabolic pathways, or Ascending cognitive streams.
    """

    @staticmethod
    def process_stimulus(
        source: str, payload: str, stimulus_type: str = "exteroceptive"
    ) -> Any:
        payload = payload.strip()

        if stimulus_type == "reflex":
            console.print(
                "[dim red]⚡ Spine intercepted crisis: Triggering Somatic Reflex Arc...[/dim red]"
            )
            try:
                from System.cli_somatic import status

                return status()
            except ImportError:
                return "Somatic reflex missing."

        if stimulus_type == "visceral":
            console.print(
                "[dim yellow]🧬 Spine routing to Enteric system (Gut)...[/dim yellow]"
            )
            from System.neuroanatomy.systemic.enteric import get_gut_reaction

            gut_reaction = get_gut_reaction(payload)
            if gut_reaction:
                return gut_reaction
            return "Gut ignores this visceral stimulus."

        console.print(
            "[dim cyan]🧠 Spine passing stimulus up to the Thalamus (Non-Blocking)...[/dim cyan]"
        )
        from System.neuroanatomy.limbic.thalamus import process_sensory_input

        # ⚡ ASYNC SHIFT: Push to Thalamus in a background thread so the Spine never blocks
        def _ascend():
            process_sensory_input(source, payload)

        threading.Thread(target=_ascend, daemon=True).start()
        return f"Stimulus from {source} successfully queued for cognitive processing."


def transduce_to_spine(
    source: str, payload: str, stimulus_type: str = "exteroceptive"
) -> Any:
    return Spine.process_stimulus(source, payload, stimulus_type)


def afferent_receptor(source_name: str, stimulus_type: str = "exteroceptive"):
    """
    Standardization Decorator for all Sense receptors.
    Automatically catches raw returns and exceptions, converting them into Spinal impulses.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                payload = str(result) if result else "Empty stimulus received."
            except Exception as e:
                # 🛡️ Auto-catch errors and route them as sensory damage reports
                payload = f"SENSORY/NETWORK ERROR: {str(e)}"

            return transduce_to_spine(source_name, payload, stimulus_type)

        return wrapper

    return decorator
