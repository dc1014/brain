import json
import subprocess
import shlex
from pathlib import Path
from rich.console import Console

console = Console()
STATE_FILE = (
    Path(__file__).parent.parent.parent / "Meta" / "Proprioception" / "motor_state.json"
)


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# FIX 1: Add the | None to satisfy Mypy
def start_process(name: str, command: str, cwd: str | None = None) -> str:
    """Starts a long-running background process securely."""
    from System.neuroanatomy.limbic.amygdala import scan_command
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.tools import ROOT_DIR

    # Amygdala Threat Scan
    is_safe_command, reason = scan_command(command)
    if not is_safe_command:
        return reason

    # Default to a safe zone (Studio) instead of ROOT_DIR
    target_cwd = cwd if cwd else str(ROOT_DIR / "Studio")
    is_safe_path, safe_cwd = validate_execution_path(target_cwd)
    if not is_safe_path:
        return safe_cwd

    state = _load_state()
    if name in state:
        return f"ERROR: Process '{name}' is already running. Please stop it first."

    # 3. Secure Execution (shell=False + shlex parsing)
    try:
        args = shlex.split(command)
        process = subprocess.Popen(
            args,
            shell=False,
            cwd=safe_cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        state[name] = {"pid": process.pid, "command": command, "cwd": safe_cwd}
        _save_state(state)
        return (
            f"SUCCESS: Process '{name}' started with PID {process.pid} in {safe_cwd}."
        )
    except Exception as e:
        return f"EXECUTION ERROR: {str(e)}"


def stop_process(name: str) -> str:
    """Stops a background process safely."""
    import psutil

    state = _load_state()
    if name not in state:
        return f"ERROR: Process '{name}' not found in state."

    pid = state[name]["pid"]
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
        del state[name]
        _save_state(state)
        return f"SUCCESS: Process '{name}' (PID {pid}) stopped."
    except psutil.NoSuchProcess:
        del state[name]
        _save_state(state)
        return f"SUCCESS: Process '{name}' was already dead. State cleaned."
    except Exception as e:
        return f"ERROR stopping process: {str(e)}"


def list_processes() -> str:
    """Lists running background processes."""
    import psutil

    state = _load_state()
    if not state:
        return "No background processes running."

    output = "Running Processes:\n"
    dead_procs = []
    for name, info in state.items():
        if psutil.pid_exists(info["pid"]):
            output += f"- {name} (PID: {info['pid']}) -> {info['command']}\n"
        else:
            dead_procs.append(name)

    if dead_procs:
        for d in dead_procs:
            del state[d]
        _save_state(state)
        output += f"\n(Cleaned up {len(dead_procs)} dead processes)"

    return output


def manage_background_process(
    action: str, name: str = "", command: str = "", cwd: str = ""
) -> str:
    """Tool interface for managing background processes."""
    action = action.lower()
    if action == "start":
        if not name or not command:
            return "ERROR: 'name' and 'command' required to start."
        return start_process(name, command, cwd)
    elif action == "stop":
        if not name:
            return "ERROR: 'name' required to stop."
        return stop_process(name)
    elif action == "list":
        return list_processes()
    else:
        return "ERROR: Invalid action. Use 'start', 'stop', or 'list'."
