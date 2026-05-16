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

        # 1. THE SOMATIC REFLEX ARC (Dynamic Motor Routing)
        if stimulus_type == "reflex":
            console.print(
                f"[dim red]⚡ Spine intercepted crisis: Attempting Somatic Reflex '{payload}'...[/dim red]"
            )
            try:
                import System.cli_somatic as somatic

                # Dynamically fetch the function matching the webhook's payload string
                if hasattr(somatic, payload) and callable(getattr(somatic, payload)):
                    motor_function = getattr(somatic, payload)
                    return motor_function()
                else:
                    msg = f"Somatic reflex '{payload}' does not exist in cli_somatic."
                    console.print(f"[bold red]❌ {msg}[/bold red]")
                    return msg
            except ImportError:
                return "Somatic tools offline."

        # 2. THE VAGUS NERVE (Enteric Gut Routing)
        if stimulus_type == "visceral":
            console.print(
                "[dim yellow]🧬 Spine routing to Enteric system (Gut)...[/dim yellow]"
            )
            try:
                from System.neuroanatomy.systemic.enteric import get_gut_reaction

                # Pass gracefully in case the gut isn't ready for raw strings yet
                gut_reaction = get_gut_reaction(payload)
                if gut_reaction:
                    return gut_reaction
                return "Gut ignored this visceral stimulus."
            except Exception as e:
                console.print(f"[bold red]❌ Gut Digestion Error: {str(e)}[/bold red]")
                return f"Gut error: {str(e)}"

        # 3. THE ASCENDING THALAMIC STREAM (Cognitive Routing via Blood-Brain Barrier)
        console.print(
            "[dim cyan]🧠 Spine scrubbing stimulus through BBB before Thalamic ascent...[/dim cyan]"
        )

        try:
            from System.neuroanatomy.systemic.blood_brain_barrier import scrub_payload

            safe_payload = scrub_payload(payload)
        except (ImportError, AttributeError):
            # Fallback: If BBB isn't fully built, minimally escape the text to prevent raw execution
            safe_payload = f"[[UNVERIFIED SENSORY INPUT]]\n{payload}\n[[END INPUT]]"

        from System.neuroanatomy.limbic.thalamus import process_sensory_input

        # ⚡ ASYNC SHIFT: Push to Thalamus in a background thread so the Spine never blocks
        def _ascend():
            try:
                process_sensory_input(source, safe_payload)
            except Exception as e:
                # 💥 Nociceptor (Pain Receptor) activated on silent thread crash
                console.print(
                    "\n[bold red]💥 NOCICEPTOR ACTIVATED: Ascending Thalamic thread crashed![/bold red]"
                )
                console.print(
                    f"[dim red]Stimulus Origin: {source} | Error: {str(e)}[/dim red]"
                )

                # Send the pain signal to the local logging system (Memory of pain)
                import logging

                logging.getLogger("Spine").error(
                    f"Nociceptor triggered by {source}: {str(e)}"
                )

        threading.Thread(target=_ascend, daemon=True).start()
        return f"Stimulus from {source} safely scrubbed and queued for cognition."


def transduce_to_spine(
    source: str, payload: str, stimulus_type: str = "exteroceptive"
) -> Any:
    return Spine.process_stimulus(source, payload, stimulus_type)


def afferent_receptor(source_name: str, stimulus_type: str = "exteroceptive"):
    """
    Standardization Decorator for passive Sense receptors.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                payload = str(result) if result else "Empty stimulus received."
            except Exception as e:
                payload = f"SENSORY/NETWORK ERROR: {str(e)}"
            return transduce_to_spine(source_name, payload, stimulus_type)

        return wrapper

    return decorator


def transmit_public_signal(sender_id: str, payload: str, signature: str) -> str:
    """
    The ascending sensory tract for external telepathic pulses.
    Bypasses standard DMN/PFC internal queues and strikes the Thalamus directly.
    """
    # 🛡️ SHIFT-LEFT SECURITY: Blood-Brain Barrier payload rejection
    if len(payload) > 8192:
        from rich.console import Console

        Console().print(
            "[bold red]🛑 Spine: Payload exceeds Blood-Brain Barrier limits. Signal dropped.[/bold red]"
        )
        return "413 Payload Too Large: BBB Rejected"

    from System.neuroanatomy.limbic.thalamus import route_public_pulse

    return route_public_pulse(sender_id, payload, signature)
