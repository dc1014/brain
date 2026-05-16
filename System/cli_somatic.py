import typer
from rich.console import Console

console = Console()


def map_topology():
    """Reflex Arc: Deterministically generates a UI-agnostic Mermaid diagram of the OS's current active topology."""
    from System.tools import map_system_topology

    console.print(
        "[dim cyan]⚡ Reflex Arc Triggered: Bypassing Prefrontal Cortex...[/dim cyan]"
    )
    result = map_system_topology()

    if "Success" in result:
        console.print("[bold green]✅ Topology mapped successfully.[/bold green]")
    else:
        console.print(f"[bold red]❌ Topology mapping failed: {result}[/bold red]")


def status():
    """Reflex Arc: Displays real-time interoceptive vitals (Token burn, Immune responses)."""
    from System.tools.diagnostic import get_system_vitals

    console.print(
        "[dim cyan]⚡ Reflex Arc Triggered: Bypassing Prefrontal Cortex...[/dim cyan]"
    )
    panel = get_system_vitals()
    console.print("\n")
    console.print(panel)
    console.print("\n")


def list_reflexes():
    """Reflex Arc: Lists all consolidated muscle memories (Engrams) in the Cerebellum."""
    from System.tools import list_engrams

    console.print(
        "[dim cyan]⚡ Reflex Arc Triggered: Querying Cerebellum...[/dim cyan]\n"
    )
    res = list_engrams()
    console.print(res)


def reflex(
    name: str = typer.Argument(
        ..., help="The name of the engram to execute (e.g., 'init_vite_react')"
    ),
    target_dir: str = typer.Argument(
        ..., help="The directory to run the reflex in (e.g., 'Studio/My-App')"
    ),
):
    """Reflex Arc: Deterministically executes a saved muscle memory (Engram) for zero tokens."""
    from System.tools import execute_engram

    console.print(
        f"[dim cyan]⚡ Reflex Arc Triggered: Firing muscle memory '{name}' directly...[/dim cyan]\n"
    )
    res = execute_engram(name, target_dir)

    if res.success:
        console.print("\n[bold green]✅ Reflex executed successfully.[/bold green]")
    else:
        console.print(f"\n[bold red]❌ Reflex failed: {res.output}[/bold red]")


def sleep():
    """Triggers the autonomic sleep cycle (Backups & Neuroplasticity)."""
    from System.neuroanatomy.autonomic.pineal import enter_sleep_cycle

    console.print("[blue]🌙 Initiating Sleep Cycle...[/blue]")
    enter_sleep_cycle()


def expose_dermis(port: int = 8080) -> str:
    """Somatic Reflex: Opens a temporary secure tunnel to the Dermis using native SSH."""
    import subprocess
    from rich.console import Console

    console = Console()

    console.print(
        f"[bold cyan]🌐 Opening secure reverse tunnel to Dermis on port {port}...[/bold cyan]"
    )
    console.print(
        "[dim yellow]Press Ctrl+C to close the tunnel and retract the skin.[/dim yellow]"
    )

    try:
        # Uses localhost.run (free, zero-install, native SSH reverse proxy)
        subprocess.run(["ssh", "-R", f"80:localhost:{port}", "nokey@localhost.run"])
        return "Tunnel closed successfully."
    except KeyboardInterrupt:
        return "Tunnel manually closed by user."
    except Exception as e:
        return f"Tunnel failure: {str(e)}"
