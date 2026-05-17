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


def flush():
    """🌊 Flushes the lymphatic system (cleans temporary logs/backups)."""
    from rich.console import Console

    console = Console()
    console.print("[dim cyan]🌊 Triggering Lymphatic Flush...[/dim cyan]")
    try:
        from System.neuroanatomy.systemic.lymphatic import flush_lymph_nodes

        flush_lymph_nodes()
        console.print("[bold green]✅ Lymphatic system flushed.[/bold green]")
    except ImportError:
        console.print(
            "[yellow]⚠️ Lymphatic routing unavailable, skipping flush.[/yellow]"
        )
    except Exception as e:
        console.print(f"[bold red]❌ Lymphatic error: {e}[/bold red]")


def sleep():
    """🌙 Forces a deep sleep cycle (Lymphatic flush + DMN Daydreaming)."""
    from rich.console import Console
    from System.neuroanatomy.autonomic.dmn import trigger_daydreams
    from System.cli_cognitive import compile

    console = Console()

    console.print("[bold blue]🌙 System entering deep sleep phase...[/bold blue]")

    # 1. Lymphatic System: Flush the biological waste (Delete old logs/cache)
    flush()

    # 2. Cerebellum: Autonomously compile recent successes into Zero-Token Engrams
    console.print(
        "[dim cyan]⚙️ Triggering Cerebellar consolidation of motor skills...[/dim cyan]"
    )
    compile()

    # 3. Default Mode Network: Dream and synthesize new ideas
    trigger_daydreams()


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


def reflex(
    engram_name: str = typer.Argument(
        ..., help="The snake_case name of the compiled engram to run."
    ),
):
    """⚡ Executes a compiled, zero-token somatic reflex (Engram) safely."""
    import sys
    import ast
    import subprocess
    from System.core.paths import ROOT_DIR
    from rich.console import Console

    console = Console()
    engram_path = ROOT_DIR / "System" / "tools" / "engrams" / f"{engram_name}.py"

    if not engram_path.exists():
        console.print(
            f"[bold red]❌ Engram '{engram_name}' not found in the Cerebellum.[/bold red]"
        )
        return

    console.print(f"[dim cyan]⚡ Firing somatic reflex: {engram_name}...[/dim cyan]")

    # 🛡️ SHIFT-LEFT SECURITY: Rapid Spinal AST Scan
    try:
        code_content = engram_path.read_text(encoding="utf-8")
        tree = ast.parse(code_content)
        dangerous_calls = {"remove", "rmdir", "rmtree", "system", "popen"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in dangerous_calls
                ):
                    console.print(
                        f"[bold red]🛑 Spinal Security Block: Engram contains dangerous call '{node.func.attr}'. Execution denied.[/bold red]"
                    )
                    return
    except SyntaxError:
        console.print("[bold red]❌ Engram is corrupted (Syntax Error).[/bold red]")
        return

    # 🛡️ ISOLATION: Subprocess Sandbox
    try:
        runner_code = (
            "import sys\n"
            f"sys.path.insert(0, '{engram_path.parent}')\n"
            f"import {engram_name}\n"
            f"{engram_name}.execute_reflex()\n"
        )

        result = subprocess.run(
            [sys.executable, "-c", runner_code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            console.print("[bold green]✅ Reflex completed successfully.[/bold green]")
            if result.stdout:
                console.print(f"[dim]{result.stdout.strip()}[/dim]")
        else:
            console.print(
                f"[bold red]❌ Reflex execution failed in subprocess:[/bold red]\n{result.stderr.strip()}"
            )

    except subprocess.TimeoutExpired:
        console.print(
            "[bold red]❌ Reflex timed out (30s limit exceeded). Motor path severed.[/bold red]"
        )
    except Exception as e:
        console.print(f"[bold red]❌ Somatic error: {e}[/bold red]")


def assimilate(
    engram_name: str = typer.Argument(
        ..., help="The quarantined engram to assimilate."
    ),
):
    """🧬 Scans a quarantined external engram and integrates it into permanent muscle memory."""
    from rich.console import Console
    from System.neuroanatomy.autonomic.cerebellum import CerebellarCompiler

    console = Console()

    console.print(
        f"[dim cyan]🧬 Initiating Spinal AST Scan on quarantined '{engram_name}'...[/dim cyan]"
    )

    compiler = CerebellarCompiler()
    success, message = compiler.assimilate_engram(engram_name)

    if success:
        console.print(f"[bold green]✅ {message}[/bold green]")
        console.print(f"[dim]Run via: uv run System/cli.py reflex {engram_name}[/dim]")
    else:
        console.print(f"[bold red]🛑 Security Block: {message}[/bold red]")
