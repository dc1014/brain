# --- System/core/onboarding/genesis.py ---
import os

# ⚡ SHIFT-LEFT: Suppress third-party LiteLLM AWS/Botocore warnings before downstream imports
os.environ["SUPPRESS_LITELLM_LOGS"] = "True"
os.environ["LITELLM_LOG"] = "ERROR"

import json
import asyncio
import urllib.request
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


def is_headless_setup() -> bool:
    return os.environ.get("CORETEX_HEADLESS", "").lower() in {"1", "true", "yes"}


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


def configure_security_gate() -> bool:
    if IS_DOCKER_RUNTIME:
        console.print(
            "[dim green][+] Containerized isolation active. Security Mode locked to Agentic Runtime.[/dim green]\n"
        )
        return True
    if is_headless_setup():
        console.print(
            "[dim green][+] Headless setup: Cognitive Mode selected by default.[/dim green]\n"
        )
        return False

    gate_text = (
        "CoreTex operates as a [bold green]Cognitive Assistant[/bold green] by default. "
        "It can freely read, organize, and write Markdown files to your Obsidian vault.\n\n"
        "To allow CoreTex to autonomously execute code and run terminal commands, you must enable Agentic Mode."
    )
    console.print(
        Panel(gate_text, title="[ EXECUTION BOUNDARIES ]", border_style="cyan")
    )

    choice = Prompt.ask(
        "\nSelect Profile\n[1] Cognitive Mode\n[2] Agentic Mode\n",
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


def innervate_senses() -> dict:
    features = {
        "vision": {
            "enabled": IS_DOCKER_RUNTIME,
            "selected": IS_DOCKER_RUNTIME,
            "name": "Occipital Vision",
        },
        "audio": {"enabled": False, "selected": False, "name": "Cochlear Audio"},
    }
    if IS_DOCKER_RUNTIME or is_headless_setup():
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


async def harvest_credentials() -> dict:
    if is_headless_setup():
        return {"USE_LOCAL_SLM": "false"}

    console.print(
        Panel(
            "Recommended: OpenRouter gives you access to every major model\n"
            "with a single key and no vendor lock-in. Get one at openrouter.ai",
            title="[ SYNAPTIC HANDSHAKE ]",
            border_style="magenta",
        )
    )
    valid_keys = {}

    choice = Prompt.ask(
        "\nSelect cloud credential strategy:\n"
        "[1] OpenRouter (Recommended)\n"
        "[2] Raw provider keys (OpenAI / Anthropic / Gemini)\n"
        "[3] Gateway/Broker (Portkey, Cloudflare AI Gateway)\n"
        "[4] Skip (Local LLMs Only)",
        choices=["1", "2", "3", "4"],
        default="1",
    )

    if choice == "1":
        key = Prompt.ask("[cyan]OpenRouter API Key[/cyan]", password=True)
        if key:
            valid_keys["OPENROUTER_API_KEY"] = key
    elif choice == "2":
        providers = {
            "OPENAI": "OpenAI API Key",
            "ANTHROPIC": "Anthropic API Key",
            "GEMINI": "Google Gemini API Key",
        }
        for prov, prompt_text in providers.items():
            key = Prompt.ask(f"[cyan]{prompt_text}[/cyan]", password=True)
            if key:
                valid_keys[f"{prov}_API_KEY"] = key
    elif choice == "3":
        console.print(
            "[dim]A custom broker intercepts traffic to providers like OpenAI or Anthropic.[/dim]"
        )
        gateway_url = Prompt.ask(
            "[cyan]Gateway Base URL (e.g., Cloudflare/Portkey)[/cyan]"
        )
        if gateway_url:
            valid_keys["GATEWAY_BASE_URL"] = gateway_url
            gateway_key = Prompt.ask(
                "[cyan]Gateway Proxy Token / API Key[/cyan]", password=True
            )
            if gateway_key:
                valid_keys["GATEWAY_API_KEY"] = gateway_key

    brave_key = Prompt.ask(
        "\n[cyan]Brave Search API Key (Optional — enables web search)[/cyan]",
        password=True,
    )
    if brave_key:
        valid_keys["BRAVE_API_KEY"] = brave_key

    ollama_detected = False
    for url in ["http://127.0.0.1:11434/api/tags", "http://localhost:11434/api/tags"]:
        try:
            urllib.request.urlopen(url, timeout=2.0)
            ollama_detected = True
            console.print(
                f"\n[bold green][+] Corpus Callosum: Local Ollama instance detected on {url}![/bold green]"
            )
            break
        except Exception:
            continue

    console.print(
        "\n[dim]CoreTex can route analytical tasks (reading files, filtering text) to a local Small Language Model (SLM) for zero-cost, high-privacy execution.[/dim]"
    )

    if Confirm.ask("[?] Enable Local SLM routing?", default=ollama_detected):
        valid_keys["USE_LOCAL_SLM"] = "true"
        local_model = Prompt.ask(
            "[cyan]Local Model Name (Requires 'ollama/' prefix for LiteLLM)[/cyan]",
            default="ollama/llama3.2",
        )
        valid_keys["LOCAL_MODEL_NAME"] = local_model
    else:
        valid_keys["USE_LOCAL_SLM"] = "false"

    return valid_keys


def bind_workspace() -> str:
    if IS_DOCKER_RUNTIME:
        console.print(
            "[bold green][+] Volumetric Isolation: Workspace hard-locked to virtual /workspace layer.[/bold green]\n"
        )
        workspace_path = Path("/workspace")
        workspace_path.mkdir(parents=True, exist_ok=True)
        for domain in ["Personal", "Professional", "Studio", "Meta", "Media"]:
            (workspace_path / domain).mkdir(parents=True, exist_ok=True)
        return "/workspace"

    # ⚡ FIX: Bind the default vault directly inside the cloned CoreTex repository
    default_path = str(ROOT_DIR / "Vault")
    console.print(
        Panel(
            "This folder becomes your knowledge vault. CoreTex will create Personal/, Professional/, "
            "Studio/, and Media/ inside it.\n\nIt's a plain Markdown folder — open it in Obsidian to get the full experience.\n\n"
            f"Default: {default_path}",
            title="[ WORKSPACE BINDING ]",
            border_style="cyan",
        )
    )

    if is_headless_setup():
        final_path = default_path
    else:
        final_path = Prompt.ask("Enter destination path (or press Enter for default)")
        if not final_path:
            final_path = default_path

    workspace_path = Path(final_path).resolve()
    workspace_path.mkdir(parents=True, exist_ok=True)

    for domain in ["Personal", "Professional", "Studio", "Meta", "Media"]:
        (workspace_path / domain).mkdir(parents=True, exist_ok=True)

    obsidian_panel = f"""Your vault is ready at: [bold green]{workspace_path}[/bold green]

  1. Open Obsidian
  2. Click "Open folder as vault"
  3. Select the path above

CoreTex will write structured Markdown notes here automatically."""

    console.print("\n")
    console.print(
        Panel(obsidian_panel, title="[ OBSIDIAN INTEGRATION ]", border_style="green")
    )

    if (not is_headless_setup()) and Confirm.ask(
        "\n[?] Open this folder now?", default=True
    ):
        import platform
        import subprocess

        os_name = platform.system()
        try:
            if os_name == "Windows":
                # Safe reflection avoids static-checking type failures on non-Windows CI environments
                getattr(os, "startfile")(str(workspace_path))
            elif os_name == "Darwin":
                subprocess.Popen(["open", str(workspace_path)])
            else:
                subprocess.Popen(["xdg-open", str(workspace_path)])
        except Exception:
            console.print(
                "[dim red]Could not automatically open the directory.[/dim red]"
            )

    return str(workspace_path)


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
        if (not is_headless_setup()) and Confirm.ask(
            "\n[?] Make 'ctx' globally accessible in your shell profile?", default=True
        ):
            bind_global_alias()
    else:
        console.print(
            "\n[dim yellow][*] Global shell alias mapping bypassed inside Docker context.[/dim yellow]\n"
        )

    next_steps = f"""Vault:    [bold green]{workspace_path}[/bold green]
Command:  [bold cyan]ctx task "summarize my week"[/bold cyan]

Next steps:
  - Open your Vault folder in Obsidian
  - Run: [cyan]ctx status[/cyan]
  - Docs: [blue]https://github.com/mrdanielcasper/coretex/wiki[/blue]

[italic]CoreTex is watching. Think out loud.[/italic]"""

    console.print("\n")
    console.print(Panel(next_steps, title="[ YOU'RE LIVE ]", border_style="green"))


if __name__ == "__main__":
    asyncio.run(main())
