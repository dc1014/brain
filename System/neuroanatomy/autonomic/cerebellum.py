from System.core.paths import ROOT_DIR
import json
import subprocess
import platform
from pathlib import Path
from System.tools import is_safe_path


ENGRAM_DIR = ROOT_DIR / "System" / "engrams"
INDEX_FILE = ENGRAM_DIR / "index.json"


def _ensure_setup():
    """Initializes the procedural memory center."""
    ENGRAM_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def save_engram(name: str, description: str, commands: str) -> str:
    """Saves a successful sequence of shell commands into muscle memory."""
    _ensure_setup()

    # Sanitize the engram name
    safe_name = "".join(c for c in name if c.isalnum() or c == "_").lower()

    # We save as cross-platform shell commands
    script_path = ENGRAM_DIR / f"{safe_name}.sh"

    # Normalize line endings to LF for cross-platform execution (Zero Debt)
    normalized_commands = commands.replace("\r\n", "\n")

    with open(script_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("#!/bin/bash\n")
        f.write(f"# {description}\n\n")
        f.write(normalized_commands)
        f.write("\n")

    # Make executable (Linux/macOS)
    try:
        script_path.chmod(0o755)
    except Exception:
        pass

    # Update the neural index
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index = json.load(f)

    index[safe_name] = {
        "description": description,
        "path": str(script_path.relative_to(ROOT_DIR).as_posix()),
    }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    return f"🧬 CEREBELLUM UPDATED: Engram '{safe_name}' permanently saved to muscle memory."


def list_engrams() -> str:
    """Returns all available muscle memory."""
    _ensure_setup()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index = json.load(f)

    if not index:
        return "The Cerebellum is currently empty. No engrams learned yet."

    output = "🧠 AVAILABLE MUSCLE MEMORY (ENGRAMS):\n"
    for name, data in index.items():
        output += f"- [{name}]: {data['description']}\n"
    return output


def execute_engram(name: str, args: str = "") -> str:
    """Fires a learned engram (script) instantaneously without LLM logic."""
    _ensure_setup()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index = json.load(f)

    safe_name = name.lower()
    if safe_name not in index:
        return f"Error: Engram '{safe_name}' not found in the Cerebellum."

    script_path = ROOT_DIR / index[safe_name]["path"]
    if not script_path.exists():
        return f"Error: Physical engram script missing at {script_path}"

    # --- SHIFT-LEFT SECURITY: Sandbox the Cerebellum ---
    current_dir = Path.cwd().resolve()
    if not is_safe_path(current_dir):
        return f"SECURITY BLOCK: Cannot execute engrams outside of the safe sandbox. Current directory: {current_dir}"

    # Execute cross-platform
    try:
        cmd = ["bash", str(script_path)]
        if args:
            cmd.extend(args.split())

        # We use shell=True on Windows if bash is not in standard path, but typically Git Bash handles it.
        use_shell = platform.system() == "Windows"

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, shell=use_shell
        )
        return f"🧬 Engram Executed Successfully:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"🛑 Engram Failed:\n{e.stderr}"
    except Exception as e:
        return f"🛑 Execution Error: {str(e)}"
