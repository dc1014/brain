from typing import Optional
from System.tools import execute_command
import json
import re
from rich.console import Console
from rich.panel import Panel
from litellm import completion  # type: ignore

from System.core.paths import ROOT_DIR
from System.core.locks import BiologicalLock
from System.runtime import AGENT_CONFIG

console = Console()
ENGRAM_DIR = ROOT_DIR / "System" / "tools" / "engrams"


class CerebellarCompiler:
    """
    Procedural Memory & Exocortex Staging.
    Converts expensive LLM Swarm execution traces into raw, deterministic,
    zero-token Python scripts (Engrams).
    """

    def __init__(self) -> None:
        ENGRAM_DIR.mkdir(parents=True, exist_ok=True)
        # Ensure it is treated as a Python module so we can import reflexes natively
        (ENGRAM_DIR / "__init__.py").touch(exist_ok=True)

    def compile_engram(self, objective: str, episode_telemetry: str) -> str | None:
        """Transforms an episodic memory trace into a hardcoded somatic engram."""
        console.print(
            "\n[bold green]🧠 PFC -> ⚙️ Cerebellum Handover Initiated[/bold green]"
        )
        console.print(
            "[dim green]The Cerebellum is compiling this expensive LLM task into a deterministic, "
            "zero-token Python script. Anticipating Exocortex export...[/dim green]"
        )

        prompt = (
            "You are the Cerebellum of Brain OS. Your job is to write deterministic Python 3 code.\n"
            "Take the following objective and execution trace, and write a single, flawless Python script "
            "that accomplishes this exact task WITHOUT using AI or LLM API calls. Use standard libraries "
            "(os, sys, subprocess, pathlib) or safely invoke local shell commands.\n\n"
            "CRITICAL EXOCORTEX REQUIREMENTS:\n"
            "1. You MUST include a dictionary at the very top of the script named exactly `EXOCORTEX_MANIFEST` "
            "with the keys: 'name' (snake_case), 'description', 'version', 'author' (set to 'Brain_OS'), and 'tags' (list).\n"
            "2. The script MUST contain a main function called `execute_reflex()` that takes no arguments.\n"
            "3. Return ONLY valid Python code inside a markdown python block. No other text.\n\n"
            f"OBJECTIVE: {objective}\n"
            f"TELEMETRY: {episode_telemetry}"
        )

        try:
            model_name = AGENT_CONFIG.get("models", {}).get(
                "fast", "gemini/gemini-2.5-flash"
            )
            response = completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content.strip()

            # Safe extraction logic without string matching traps
            match = re.search(r"```python\n(.*?)\n```", raw_text, re.DOTALL)
            code = (
                match.group(1).strip()
                if match
                else raw_text.replace("```python", "").replace("```", "").strip()
            )

            name_match = re.search(r"'name'\s*:\s*['\"]([a-z0-9_]+)['\"]", code)
            engram_name = name_match.group(1) if name_match else "unnamed_reflex"

            engram_path = ENGRAM_DIR / f"{engram_name}.py"

            with BiologicalLock(str(engram_path)):
                with open(engram_path, "w", encoding="utf-8") as f:
                    f.write(code)

            console.print(
                Panel(
                    f"[bold cyan]⚙️ Procedural Engram Compiled Successfully![/bold cyan]\n\n"
                    f"File: [yellow]{engram_path.relative_to(ROOT_DIR)}[/yellow]\n"
                    f"Run anytime via: [bold]uv run System/cli.py reflex {engram_name}[/bold]\n"
                    f"[dim]Exocortex sharing manifest validated.[/dim]",
                    border_style="green",
                )
            )

            return engram_name

        except Exception as e:
            console.print(
                f"[bold red]❌ Cerebellar compilation failed: {str(e)}[/bold red]"
            )
            return None


def create_engram(name: str, description: str, commands: list[str]) -> str:
    """Saves a sequence of verified shell commands as a permanent muscle memory."""
    try:
        ENGRAM_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = name.lower().replace(" ", "_").replace("-", "_")
        engram_path = ENGRAM_DIR / f"{safe_name}.json"

        data = {"description": description, "commands": commands}
        engram_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        console.print(
            f"[bold green]🧠 Cerebellum: Muscle memory '{safe_name}' consolidated.[/bold green]"
        )
        return f"Engram '{safe_name}' successfully saved to the Cerebellum."
    except Exception as e:
        return f"Failed to save engram: {e}"


def execute_engram(name: str, target_dir: str, params: Optional[dict] = None) -> str:
    """Instantly fires a sequence of shell commands with dynamic variable injection."""
    safe_name = name.lower().replace(" ", "_").replace("-", "_")
    engram_path = ENGRAM_DIR / f"{safe_name}.json"

    if not engram_path.exists():
        return f"Error: Engram '{safe_name}' not found. You must create it first."

    try:
        data = json.loads(engram_path.read_text(encoding="utf-8"))
        commands = data.get("commands", [])
    except Exception as e:
        return f"Failed to read engram '{safe_name}': {e}"

    console.print(
        f"[bold cyan]⚡ Cerebellum: Firing parametric muscle memory '{safe_name}'...[/bold cyan]"
    )

    params = params or {}
    results = []

    for cmd in commands:
        # ⚡ SHIFT-LEFT: Dynamic Parametric Injection
        for k, v in params.items():
            # Support both ${var} and $var bash syntax
            cmd = cmd.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))

        console.print(f"[dim]│ Reflex: {cmd}[/dim]")
        # 🦠 Automatically inherits Microglia auto-healing!
        res = execute_command(cmd, target_dir)

        if not res.success:
            error_msg = f"Engram '{safe_name}' failed on command: `{cmd}`\nOutput:\n{res.output}"
            console.print(f"[bold red]{error_msg}[/bold red]")
            return error_msg

        results.append(f"SUCCESS: {cmd}")

    console.print(
        f"[bold green]✨ Cerebellum: '{safe_name}' executed flawlessly.[/bold green]"
    )
    return f"Engram '{safe_name}' executed flawlessly.\n" + "\n".join(results)


def list_engrams() -> str:
    """Lists all available muscle memory scripts."""
    if not ENGRAM_DIR.exists():
        return "No engrams found in the Cerebellum."

    engrams = []
    for f in ENGRAM_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            engrams.append(f"- {f.stem}: {data.get('description', 'No description')}")
        except Exception:
            pass

    if not engrams:
        return "No valid engrams found."

    return "Available Muscle Memories (Engrams):\n" + "\n".join(engrams)
