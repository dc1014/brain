import json
from typing import Optional
from rich.console import Console
from System.core.paths import ROOT_DIR
from System.tools.execution import execute_command

console = Console()
ENGRAM_DIR = ROOT_DIR / "Meta" / "Engrams"


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
