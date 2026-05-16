from typing import Any
from rich.console import Console

console = Console()


class Spine:
    """
    The Spine (Central Inbound Pathway).
    Routes raw sensory stimuli to Somatic Reflexes (0 tokens),
    Metabolic pathways (0 tokens), or Ascending cognitive streams.
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
            "[dim cyan]🧠 Spine passing stimulus up to the Thalamus...[/dim cyan]"
        )
        from System.neuroanatomy.limbic.thalamus import process_sensory_input

        return process_sensory_input(source, payload)


def transduce_to_spine(
    source: str, payload: str, stimulus_type: str = "exteroceptive"
) -> Any:
    return Spine.process_stimulus(source, payload, stimulus_type)
