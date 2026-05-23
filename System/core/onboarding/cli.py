# --- System/core/onboarding/cli.py ---
import sys
import json
import asyncio
import secrets
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
from System.core.onboarding.synapses import verify_api_key, scan_ollama
from System.core.onboarding.vault import (
    sniff_vault_paths,
    setup_obsidian_shell_commands,
)
from System.core.onboarding.path_binding import bind_global_alias

console = Console()
ENV_PATH = ROOT_DIR / ".env"
FEATURES_PATH = ROOT_DIR / "System" / "config" / "features.json"


# --- 1. THE AWAKENING ---
def draw_brain():
    console.clear()
    brain_art = """[bold cyan]
      🧠  B R A I N  ::  S Y N A P T I C   G E N E S I S  🧠
      ──────────────────────────────────────────────────────────
               [ Cortical / Autonomic / Limbic Control Plane ]
    [/bold cyan]"""
    console.print(brain_art)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component Path")
    table.add_column("System Target")
    table.add_column("Native Footprint")
    table.add_column("Operational Status")

    table.add_row(
        "System/core/",
        "Core Executive NLP Matrix",
        "Ultra-Lightweight",
        "[bold green][ READY ][/bold green]",
    )
    table.add_row(
        "System/neuroanatomy/",
        "SQLite FTS5 Indexing Layer",
        "Local Memory",
        "[bold green][ READY ][/bold green]",
    )
    table.add_row(
        "Sense/receptors/",
        "Optional Sensory Organs",
        "Progressive Enhancement",
        "[dim yellow][ DORMANT ][/dim yellow]",
    )
    console.print(table)
    console.print("\n")


# --- 2. SECURITY GATE ---
def configure_security_gate() -> bool:
    gate_text = (
        "Brain operates as a [bold green]SAFE, READ-ONLY[/bold green] Second Brain by default.\n\n"
        "To allow the AI to unlock its Motor Cortex—granting it autonomy to execute terminal "
        "commands and write code—you must explicitly opt in.\n\n"
        "[bold red]RISK WARNING:[/bold red] Autonomous mode allows an LLM to invoke subprocesses. "
        "Enabling this requires trust in your provider's alignment guards."
    )
    console.print(
        Panel(
            gate_text, title="🔐 [ SHIFT-LEFT SECURITY GATEWAY ] 🔐", border_style="red"
        )
    )

    console.print("🎛️  [bold]Select your Cognitive Agency Profile:[/bold]")
    console.print(
        "  [bold cyan][1][/bold cyan] Advisory Mode (Read-Only, Safe-by-Default) [dim][RECOMMENDED][/dim]"
    )
    console.print(
        "  [bold cyan][2][/bold cyan] Autonomous Mode (Read/Write, Container Sandboxed Execution)"
    )

    choice = Prompt.ask("\nSelect Profile", choices=["1", "2"], default="1")
    if choice == "1":
        console.print(
            "[dim green]Advisory Mode selected. System remains fully read-only.[/dim green]\n"
        )
        return False

    console.print("\n[bold yellow]⚠️ INTENTIONAL OVERRIDE DETECTED.[/bold yellow]")
    override = Prompt.ask(
        "To release motor inhibition filters, type [bold]ENABLE[/bold] (or press Enter to abort)"
    )

    if override.strip() == "ENABLE":
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Interrogating OS for secure Deno WASM sandbox...[/cyan]"),
            transient=True,
        ) as progress:
            progress.add_task("", total=None)
            if verify_deno_sandbox():
                console.print(
                    "[bold green]✅ Secure WASM Sandbox verified: Deno Runtime detected.[/bold green]\n"
                )
                return True
            else:
                fail_msg = (
                    "[bold red]❌ CONTAINER ENGINE MISSING:[/bold red] Sandboxed code execution requires the Deno runtime.\n\n"
                    "To preserve maximum stability, Brain has safely forced your profile back to [bold green][ Advisory Mode ][/bold green].\n\n"
                    "To unlock full autonomy later, install Deno and rerun setup:\n"
                    "👉 macOS/Linux: [cyan]curl -fsSL https://deno.land/install.sh | sh[/cyan]\n"
                    "👉 Windows:     [cyan]irm https://deno.land/install.ps1 | iex[/cyan]"
                )
                console.print(Panel(fail_msg, border_style="red"))
                return False

    console.print("[dim green]Override aborted. Advisory Mode enforced.[/dim green]\n")
    return False


# --- 3. SENSES ---
def innervate_senses() -> dict:
    features = {
        "vision": {"enabled": False, "selected": False, "name": "Occipital Vision"},
        "audio": {"enabled": False, "selected": False, "name": "Cochlear Audio"},
    }

    console.print(
        Panel(
            "Optional senses require heavy binaries. They will be installed cleanly into your local `.venv`.",
            title="🧬 [ PROGRESSIVE SENSORY INNERVATION ] 🧬",
            border_style="blue",
        )
    )

    if Confirm.ask(
        "👁️ Enable the Retina? (Vision / Multimodal web scraping +150MB)", default=False
    ):
        features["vision"]["selected"] = True
    if Confirm.ask(
        "👂 Enable the Cochlea? (Audio / Speech input +50MB)", default=False
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
                    progress.add_task(
                        description="[cyan]Downloading Chromium Engine (Timeout: 60s)...[/cyan]",
                        total=None,
                    )
                    if not install_playwright_chromium(timeout_seconds=60):
                        console.print(
                            "[bold yellow]⚠️ Vision download timed out. Continuing without Chromium.[/bold yellow]"
                        )
                        data["enabled"] = False

    console.print("[bold green]✅ Sensory map established.[/bold green]\n")
    return features


# --- 4. SYNAPSES (Cloud & Local LLMs) ---
async def harvest_credentials() -> dict:
    console.print(
        Panel(
            "Leave blank to skip. Skipped models will be bypassed during routing.",
            title="🔑 [ SYNAPTIC HANDSHAKE ] 🔑",
            border_style="magenta",
        )
    )

    valid_keys = {}

    # Check for Local AI Engine
    if Confirm.ask(
        "🦙 Are you running a local Ollama instance for private AI inference?",
        default=False,
    ):
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Scanning localhost:11434 for Ollama...[/cyan]"),
            transient=True,
        ) as progress:
            progress.add_task("", total=None)
            if await scan_ollama():
                console.print(
                    "[bold green]✅ Local Ollama engine detected and bound.[/bold green]\n"
                )
                valid_keys["OLLAMA_API_BASE"] = "http://localhost:11434"
            else:
                console.print(
                    "[bold yellow]⚠️ Could not connect to Ollama. Ensure the daemon is running.[/bold yellow]\n"
                )

    # Check for Cloud Providers
    providers = {
        "OPENAI": {
            "prompt": "OpenAI API Key (gpt-4o-mini)",
            "model": "openai/gpt-4o-mini",
            "key": "",
        },
        "ANTHROPIC": {
            "prompt": "Anthropic API Key (claude-3-5-haiku)",
            "model": "anthropic/claude-3-5-haiku-20241022",
            "key": "",
        },
        "GEMINI": {
            "prompt": "Google Gemini API Key (gemini-2.5-flash)",
            "model": "gemini/gemini-2.5-flash",
            "key": "",
        },
        "OPENROUTER": {
            "prompt": "OpenRouter API Key (sk-or-v1-...)",
            "model": "openrouter/auto",
            "key": "",
        },
    }

    for prov, data in providers.items():
        data["key"] = Prompt.ask(f"[cyan]{data['prompt']}[/cyan]", password=True)

    console.print("\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[magenta]Verifying live API quotas...[/magenta]"),
        transient=True,
    ) as progress:
        progress.add_task("", total=None)

        tasks = [
            verify_api_key(prov, data["key"], data["model"])
            for prov, data in providers.items()
        ]
        results = await asyncio.gather(*tasks)

        for (prov, data), is_valid in zip(providers.items(), results):
            if is_valid:
                valid_keys[f"{prov}_API_KEY"] = data["key"]
                console.print(
                    f"[bold green]✅ {prov}: Verified and active.[/bold green]"
                )
            elif data["key"]:
                console.print(
                    f"[bold red]❌ {prov}: Key provided, but rejected (Check quota/billing).[/bold red]"
                )

    console.print("\n")
    return valid_keys


# --- 5. NEURAL CRYPTOGRAPHY ---
def configure_neural_cryptography() -> str:
    console.print(
        Panel(
            "Brain can generate a unique cryptographic identity key. "
            "This allows you to securely encrypt memory backups or securely 'share brains' "
            "with other instances over peer-to-peer networks.",
            title="🧬 [ NEURAL CRYPTOGRAPHY ] 🧬",
            border_style="green",
        )
    )

    if Confirm.ask("Generate a secure identity key for this Brain?", default=True):
        crypto_key = secrets.token_urlsafe(32)
        console.print(
            "[bold green]✅ Cryptographic Identity Key generated and secured.[/bold green]\n"
        )
        return crypto_key

    console.print(
        "[dim yellow]⚠️ Cryptographic sharing disabled. You can generate one later.[/dim yellow]\n"
    )
    return ""


# --- 6. VAULT BINDING ---
# --- Update in System/core/onboarding/cli.py ---
def bind_vault() -> str:
    console.print(
        Panel(
            "Brain integrates natively with Obsidian markdown vaults.",
            title="📁 [ SPATIAL BINDING ] 📁",
            border_style="cyan",
        )
    )

    vaults = sniff_vault_paths()
    final_path = ""

    if vaults:
        vault_paths = list(vaults.values())
        if len(vault_paths) == 1:
            if Confirm.ask(
                f"Found Obsidian vault at [bold cyan]{vault_paths[0]}[/bold cyan]. Bind to this directory?",
                default=True,
            ):
                final_path = vault_paths[0]
        else:
            console.print("[bold cyan]Multiple Obsidian Vaults detected:[/bold cyan]")
            for i, p in enumerate(vault_paths):
                console.print(f"  [{i}] {p}")
            choice = Prompt.ask(
                "Select vault index to bind",
                choices=[str(i) for i in range(len(vault_paths))],
                default="0",
            )
            final_path = vault_paths[int(choice)]

    if not final_path:
        final_path = Prompt.ask(
            "Drag-and-drop your Vault folder into this terminal and press Enter"
        ).strip("'\" ")

    if final_path and setup_obsidian_shell_commands(Path(final_path)):
        console.print(
            "[bold green]✅ Brain OS controls & hotkeys (Ctrl+Alt+S) auto-enabled in Obsidian![/bold green]\n"
        )
    else:
        console.print(
            "[bold yellow]⚠️ Could not automatically inject hotkeys. Proceeding with binding...[/bold yellow]\n"
        )

    return final_path


# --- MASTER EXECUTION ORCHESTRATOR ---
async def main():
    draw_brain()

    # Execute exactly in sequential, decoupled phases
    code_execution_enabled = configure_security_gate()
    features = innervate_senses()
    valid_keys = await harvest_credentials()
    crypto_key = configure_neural_cryptography()
    vault_path = bind_vault()

    with Progress(
        SpinnerColumn(),
        TextColumn("[green]Serializing system state...[/green]"),
        transient=True,
    ) as progress:
        progress.add_task("", total=None)

        # 1. Safely write environment variables
        env_content = (
            f"BRAIN_ENABLE_CODE_EXECUTION={str(code_execution_enabled).lower()}\n"
        )
        env_content += f"BRAIN_VAULT_PATH={vault_path}\n"
        if crypto_key:
            env_content += f"BRAIN_CRYPTO_KEY={crypto_key}\n"
        for k, v in valid_keys.items():
            env_content += f"{k}={v}\n"

        _atomic_write_text(ENV_PATH, env_content)

        # 2. Write physical sensory capabilities payload
        FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(FEATURES_PATH, json.dumps(features, indent=4))

    # 3. Inject global shell profile alias
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Binding global neural pathways (adding to PATH)...[/cyan]"),
        transient=True,
    ) as progress:
        progress.add_task("", total=None)
        if bind_global_alias():
            console.print(
                "[bold green]✅ Global alias 'brain' injected into shell profile![/bold green]"
            )
        else:
            console.print(
                "[dim yellow]⚠️ Could not auto-bind shell profile. You can manually alias 'brain' later.[/dim yellow]"
            )

    # 4. Handoff
    console.print("\n[bold green]🎉 SYNAPTIC GENESIS COMPLETE 🎉[/bold green]")
    console.print("Restart your terminal to load the alias, then simply run:\n")
    console.print("  [bold cyan]brain[/bold cyan]\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[dim red]Genesis aborted by user.[/dim red]")
        sys.exit(1)
