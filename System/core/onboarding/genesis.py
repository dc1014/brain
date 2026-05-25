# --- System/core/onboarding/genesis.py ---
import json
import asyncio
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from System.core.paths import ROOT_DIR
from System.core.onboarding.security import verify_deno_sandbox, _atomic_write_text
from System.core.onboarding.senses import (
    install_optional_feature,
    install_playwright_chromium,
)
from System.core.onboarding.path_binding import bind_global_alias
from System.core.onboarding.vendor_sandbox import vendor_offline_sandbox

console = Console()
ENV_PATH = ROOT_DIR / ".env"
FEATURES_PATH = ROOT_DIR / "System" / "config" / "features.json"

IS_DOCKER_RUNTIME = (
    Path("/.dockerenv").exists() or os.environ.get("CORETEX_CONTAINER_TRACK") == "1"
)


# --- 1. THE AWAKENING ---
def draw_coretex():
    console.clear()
    coretex_art = """[bold cyan]
 ██████╗ ██████╗ ██████╗ ███████╗████████╗███████╗██╗  ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝╚██╗██╔╝
██║     ██║   ██║██████╔╝█████╗     ██║   █████╗   ╚███╔╝
██║     ██║   ██║██╔══██╗██╔══╝     ██║   ██╔══╝   ██╔██╗
╚██████╗╚██████╔╝██║  ██║███████╗   ██║   ███████╗██╔╝ ██╗
 ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚══╝
    [/bold cyan]"""
    console.print(coretex_art)
    console.print(
        f"       [dim]Biomimetic AI Control Plane And Obsidian Vault // Synaptic Genesis [Context: {'Docker' if IS_DOCKER_RUNTIME else 'Host'}] [/dim]\n"
    )

    table = Table(show_header=True, header_style="bold cyan", box=None)
    table.add_column("Neural Pathway")
    table.add_column("Subsystem Target")
    table.add_column("Status", justify="right")

    table.add_row(
        "System/core/", "Executive NLP Routing Matrix", "[bold green]READY[/bold green]"
    )
    table.add_row(
        "System/neuroanatomy/",
        "Structural Ledger & Indexing",
        "[bold green]READY[/bold green]",
    )
    table.add_row(
        "Sense/receptors/",
        "Progressive Sensory Organs",
        "[bold green]READY[/bold green]"
        if IS_DOCKER_RUNTIME
        else "[dim yellow]DORMANT[/dim yellow]",
    )

    console.print(table)
    console.print("\n")


# --- 2. SECURITY GATE ---
def configure_security_gate() -> bool:
    if IS_DOCKER_RUNTIME:
        console.print(
            "[dim green][+] Containerized isolation active. Security Mode locked to Agentic Runtime.[/dim green]\n"
        )
        return True

    gate_text = (
        "CoreTex operates as a [bold green]Cognitive Assistant[/bold green] by default. "
        "It can freely read, organize, and write Markdown files to your Obsidian vault.\n\n"
        "To allow CoreTex to autonomously execute code and run terminal commands, you must enable Agentic Mode."
    )
    console.print(
        Panel(gate_text, title="[ EXECUTION BOUNDARIES ]", border_style="cyan")
    )

    choice = Prompt.ask(
        "\nSelect Profile\n[1] Cognitive Mode\n[2] Agentic Mode",
        choices=["1", "2"],
        default="1",
    )
    if choice == "1":
        return False

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Interrogating OS for secure Deno WASM sandbox...[/cyan]"),
        transient=True,
    ) as progress:
        progress.add_task("", total=None)
        return verify_deno_sandbox()


# --- 3. SENSES ---
def innervate_senses() -> dict:
    features = {
        "vision": {
            "enabled": IS_DOCKER_RUNTIME,
            "selected": IS_DOCKER_RUNTIME,
            "name": "Occipital Vision",
        },
        "audio": {"enabled": False, "selected": False, "name": "Cochlear Audio"},
    }
    if IS_DOCKER_RUNTIME:
        return features

    if Confirm.ask(
        "[?] Enable the Retina? (Vision / Multimodal web scraping +150MB)",
        default=False,
    ):
        features["vision"]["selected"] = True
    if Confirm.ask(
        "[?] Enable the Cochlea? (Audio / Speech input +50MB)", default=False
    ):
        features["audio"]["selected"] = True

    for sense, data in features.items():
        if data["selected"]:
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[cyan]Installing {sense.capitalize()} pathways...[/cyan]"),
                transient=True,
            ) as progress:
                progress.add_task("", total=None)
                if install_optional_feature(sense):
                    data["enabled"] = True
                if sense == "vision" and data["enabled"]:
                    install_playwright_chromium(timeout_seconds=60)
    return features


# --- 4. SYNAPSES (Cloud & Local LLMs) ---
async def harvest_credentials() -> dict:
    console.print(
        Panel(
            "Leave blank to skip provider mapping registers.",
            title="[ SYNAPTIC HANDSHAKE ]",
            border_style="magenta",
        )
    )
    valid_keys = {}

    providers = {
        "OPENAI": {"prompt": "OpenAI API Key", "model": "openai/gpt-4o-mini"},
        "ANTHROPIC": {
            "prompt": "Anthropic API Key",
            "model": "anthropic/claude-3-5-haiku-20241022",
        },
        "GEMINI": {
            "prompt": "Google Gemini API Key",
            "model": "gemini/gemini-2.5-flash",
        },
        "OPENROUTER": {
            "prompt": "OpenRouter API Key",
            "model": "openrouter/auto",
        },
    }

    for prov, data in providers.items():
        key = Prompt.ask(f"[cyan]{data['prompt']}[/cyan]", password=True)
        if key:
            valid_keys[f"{prov}_API_KEY"] = key

    brave_key = Prompt.ask(
        "[cyan]Brave Search API Key (Required for web search tools)[/cyan]",
        password=True,
    )
    if brave_key:
        valid_keys["BRAVE_API_KEY"] = brave_key

    return valid_keys


# --- 5. WORKSPACE BINDING ---
def bind_workspace() -> str:
    if IS_DOCKER_RUNTIME:
        console.print(
            "[bold green][+] Volumetric Isolation: Workspace hard-locked to virtual /workspace layer.[/bold green]\n"
        )
        workspace_path = Path("/workspace")
        workspace_path.mkdir(parents=True, exist_ok=True)
        # Restore scaffolding regression
        for domain in ["Personal", "Professional", "Studio", "Meta", "Media"]:
            (workspace_path / domain).mkdir(parents=True, exist_ok=True)
        return "/workspace"

    console.print(
        Panel(
            "CoreTex OS operates on plain text. Bind it to any local folder.",
            title="[ WORKSPACE BINDING ]",
            border_style="cyan",
        )
    )
    final_path = Prompt.ask("Drag-and-drop or write a folder destination path string")
    if not final_path:
        final_path = str(Path.home() / "CoreTex_Workspace")

    workspace_path = Path(final_path)
    workspace_path.mkdir(parents=True, exist_ok=True)

    # Restore scaffolding regression
    for domain in ["Personal", "Professional", "Studio", "Meta", "Media"]:
        (workspace_path / domain).mkdir(parents=True, exist_ok=True)

    return str(workspace_path)


# --- MASTER EXECUTION ORCHESTRATOR ---
async def main():
    draw_coretex()

    code_execution_enabled = configure_security_gate()
    features = innervate_senses()
    valid_keys = await harvest_credentials()
    workspace_path = bind_workspace()

    if not IS_DOCKER_RUNTIME:
        vendor_offline_sandbox(ROOT_DIR)

    with Progress(
        SpinnerColumn(),
        TextColumn("[green]Serializing system state...[/green]"),
        transient=True,
    ) as progress:
        progress.add_task("", total=None)

        env_content = (
            f"CORETEX_ENABLE_CODE_EXECUTION={str(code_execution_enabled).lower()}\n"
        )
        env_content += f"CORETEX_VAULT_PATH={workspace_path}\n"
        for k, v in valid_keys.items():
            env_content += f"{k}={v}\n"

        _atomic_write_text(ENV_PATH, env_content)
        FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(FEATURES_PATH, json.dumps(features, indent=4))

    if not IS_DOCKER_RUNTIME:
        if Confirm.ask(
            "\n[?] Make 'ctx' globally accessible in your shell profile?", default=True
        ):
            bind_global_alias()
    else:
        console.print(
            "\n[dim yellow][*] Global shell alias mapping bypassed inside Docker context.[/dim yellow]\n"
        )

    console.print("\n[bold green][+] SYNAPTIC GENESIS COMPLETE [+][/bold green]\n")


if __name__ == "__main__":
    asyncio.run(main())
