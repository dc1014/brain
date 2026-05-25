import typer
import subprocess
import sys
import ast
import json
import time
import os
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console
from System.core.paths import ROOT_DIR
from System.neuroanatomy.cortical.mirror_neurons import MirrorNeurons

console = Console()


def map_topology():
    """Reflex Arc: Deterministically generates a UI-agnostic Mermaid diagram of the OS's current active topology."""
    from System.tools import map_system_topology

    console.print(
        "[dim cyan]⚡ Reflex Arc Triggered: Bypassing Prefrontal Cortex...[/dim cyan]"
    )

    result = map_system_topology("mermaid")

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
    """🌙 Forces a deep sleep cycle (Lymphatic flush + DMN Daydreaming + DB Compaction)."""
    from rich.console import Console
    from System.neuroanatomy.autonomic.dmn import trigger_daydreams
    from System.cli_cognitive import compile

    console = Console()

    console.print("[bold blue]🌙 System entering deep sleep phase...[/bold blue]")

    flush()

    console.print(
        "[dim cyan]⚙️ Triggering Cerebellar consolidation of motor skills...[/dim cyan]"
    )
    compile()

    console.print(
        "[dim cyan]🧠 Cortical Consolidation: Re-sampling multi-file style baselines...[/dim cyan]"
    )
    try:
        mn = MirrorNeurons()
        mn.consolidate_stylistic_baseline()
    except Exception as e:
        console.print(
            f"[dim red]❌ Stylistic baseline consolidation skipped: {e}[/dim red]"
        )

    console.print(
        "[dim cyan]📚 Limbic Compression: Compacting heavy memories into semantic sidecars...[/dim cyan]"
    )
    try:
        from System.neuroanatomy.limbic.hippocampus import run_semantic_compaction_sweep

        run_semantic_compaction_sweep()
    except Exception as e:
        console.print(f"[dim red]❌ Semantic compaction skipped: {e}[/dim red]")

    trigger_daydreams()

    try:
        from System.neuroanatomy.systemic.lymphatic import trigger_lymphatic_sweep_sync

        trigger_lymphatic_sweep_sync()
    except Exception as e:
        console.print(f"[dim red]❌ Somatic sleep sweep skipped: {e}[/dim red]")

    console.print(
        "[bold green]💤 Sleep cycle completed flawlessly. CoreTex OS is fully optimized.[/bold green]"
    )


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
    engram_path = ROOT_DIR / "System" / "tools" / "engrams" / f"{engram_name}.py"

    if not engram_path.exists():
        console.print(
            f"[bold red]❌ Engram '{engram_name}' not found in the Cerebellum.[/bold red]"
        )
        return

    console.print(f"[dim cyan]⚡ Firing somatic reflex: {engram_name}...[/dim cyan]")

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
    from System.neuroanatomy.autonomic.cerebellum import CerebellarCompiler

    console = Console()

    console.print(
        f"[dim cyan]🧬 Initiating Spinal AST Scan on quarantined '{engram_name}'...[/dim cyan]"
    )

    compiler = CerebellarCompiler()
    success, message = compiler.assimilate_engram(engram_name)

    if success:
        console.print(f"[bold green]✅ {message}[/bold green]")
        # FIX: Rebranded console tracking syntax guidelines to use the ctx shortcut format
        console.print(f"[dim]Run via: ctx reflex {engram_name}[/dim]")
    else:
        console.print(f"[bold red]🛑 Security Block: {message}[/bold red]")


def watch(max_loops: Optional[int] = typer.Option(None, hidden=True)):
    """🫁 Somatosensory Cortex: File watcher daemon (Respiratory system)."""
    if not isinstance(max_loops, int):
        max_loops = None

    mn = MirrorNeurons()
    mtime_cache: Dict[str, float] = {}
    pending_quantization: Dict[str, float] = {}

    core_domains = ["Studio", "Personal", "Professional", "Meta"]
    ignore_parts = {".git", "__pycache__", ".venv", ".trash", "node_modules"}

    def _discover_files() -> None:
        current_tracked = set()
        for domain in core_domains:
            domain_path = ROOT_DIR / domain
            if not domain_path.exists():
                continue
            for root, dirs, files in os.walk(str(domain_path)):
                dirs[:] = [d for d in dirs if d not in ignore_parts]
                for file in files:
                    if file.endswith((".py", ".md")):
                        full_path = os.path.join(root, file).replace("\\", "/")
                        current_tracked.add(full_path)
                        if full_path not in mtime_cache:
                            try:
                                mtime_cache[full_path] = Path(full_path).stat().st_mtime
                            except OSError:
                                pass

        for cached_path in list(mtime_cache.keys()):
            if cached_path not in current_tracked:
                mtime_cache.pop(cached_path, None)
                pending_quantization.pop(cached_path, None)

    _discover_files()
    console.print(
        "[bold green]🫁 Somatosensory Cortex: Watchdog initialized active...[/bold green]"
    )

    loop_count = 0
    last_tonic_sweep = time.time()

    while True:
        if max_loops is not None and loop_count >= max_loops:
            break
        loop_count += 1

        time.sleep(1)
        now = time.time()

        for full_path in list(mtime_cache.keys()):
            try:
                if not os.path.exists(full_path):
                    mtime_cache.pop(full_path, None)
                    pending_quantization[full_path] = now
                    continue

                current_mtime = Path(full_path).stat().st_mtime
                old_mtime = mtime_cache.get(full_path)

                if old_mtime is not None and current_mtime > old_mtime:
                    mtime_cache[full_path] = current_mtime
                    pending_quantization[full_path] = now
                    file_name = os.path.basename(full_path)
                    console.print(
                        f"[dim yellow]🦠 Quantization: File '{file_name}' modified. Entering refractory window...[/dim yellow]"
                    )
            except OSError:
                pass

        for full_path in list(pending_quantization.keys()):
            if now - pending_quantization[full_path] >= 3.0:
                try:
                    file_name = os.path.basename(full_path)
                    if os.path.exists(full_path):
                        content = Path(full_path).read_text(encoding="utf-8")
                        mode = "code" if file_name.endswith(".py") else "prose"
                        mn.analyze_and_mirror_style(content, mode=mode)
                        console.print(
                            f"[bold green]🧠 Refractory Window Closed: Stylistic mirror re-profiled via '{file_name}'[/bold green]"
                        )
                    pending_quantization.pop(full_path, None)
                except Exception:
                    pending_quantization.pop(full_path, None)

        if now - last_tonic_sweep >= 10.0 or max_loops is not None:
            _discover_files()
            last_tonic_sweep = now


def observe(
    agent_id: str = typer.Argument(..., help="Identifier of the observed sub-agent."),
    objective: str = typer.Argument(
        ..., help="The explicit objective description string."
    ),
    steps: str = typer.Argument(
        ..., help="Comma-separated chain of successful terminal execution commands."
    ),
) -> None:
    """🧠 Mirror Neurons: Instructs the cortex to track and log a successful peer multi-agent timeline track."""
    mn = MirrorNeurons()
    command_list = [s.strip() for s in steps.split(",") if s.strip()]
    mn.observe_and_record(agent_id, objective, command_list)


def sync_mirror(
    prompt: str = typer.Argument(
        ..., help="The incoming developer prompt string to replicate."
    ),
) -> None:
    """🧠 Mirror Neurons: Queries observed peer arrays to instantly replicate execution tracks for zero tokens."""
    mn = MirrorNeurons()
    track = mn.synchronize_muscle_memory(prompt)
    if track:
        console.print(
            "[bold green]✨ Mirror Match Found! Executing cached behavioral track shortcuts natively:[/bold green]"
        )
        console.print(json.dumps(track, indent=2))
    else:
        console.print(
            "[yellow]🔍 Mirror Cache Miss: Intent unrecorded. Routing to active cognitive pathways.[/yellow]"
        )


def imitate(
    path: Path = typer.Argument(
        ...,
        help="Path to the file script or obsidian note text to profile style metrics from.",
    ),
    mode: str = typer.Option(
        "code",
        help="Tuning execution pass type: 'code' or 'prose' contract validation marker.",
    ),
) -> None:
    """🧠 Mirror Neurons: Ingests a plaintext layout configuration file to dynamically fingerprint your personalized style cadences."""
    if not path.exists():
        console.print(f"[bold red]🛑 File not found: '{path}'[/bold red]")
        return

    try:
        content = path.read_text(encoding="utf-8")
        mn = MirrorNeurons()
        mn.analyze_and_mirror_style(content, mode)
        console.print(
            f"[bold green]✅ Synaptic Style Card updated successfully via target: {path.name}[/bold green]"
        )
    except Exception as e:
        console.print(
            f"[bold red]Stylistic fingerprint extraction error: {e}[/bold red]"
        )
