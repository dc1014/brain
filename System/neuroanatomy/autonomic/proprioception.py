import json
import subprocess
import shlex
import atexit
import socket
import time
import sys
from typing import Optional
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


def sweep_zombies() -> None:
    """Kills all tracked processes to prevent port locking on shutdown."""
    import psutil

    state = _load_state()
    if not state:
        return

    killed_count = 0
    for name, info in list(state.items()):
        pid = info.get("pid")
        if not pid:
            continue
        try:
            if psutil.pid_exists(pid):
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                killed_count += 1
        except Exception:
            pass

    if killed_count > 0:
        # Use native print as rich console may be torn down during OS exit
        print(
            f"\n🧠 Proprioception: Swept {killed_count} zombie processes on shutdown."
        )

    _save_state({})


# ⚡ ZERO-DEBT: Bind the death sweep to the OS lifecycle
atexit.register(sweep_zombies)


def is_port_in_use(port: int) -> bool:
    """Proprioceptive sensory check: verifies if a port is actually transmitting."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def start_process(
    name: str, command: str, cwd: str | None = None, port: Optional[int] = None
) -> str:
    """Starts a long-running background process securely."""
    from System.neuroanatomy.limbic.amygdala import scan_command
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.core.paths import ROOT_DIR
    import psutil

    # Amygdala Threat Scan
    is_safe_command, reason = scan_command(command)
    if not is_safe_command:
        return reason

    target_cwd = cwd if cwd else str(ROOT_DIR / "Studio")
    is_safe_path, safe_cwd = validate_execution_path(target_cwd)
    if not is_safe_path:
        return safe_cwd

    state = _load_state()
    if name in state:
        if psutil.pid_exists(state[name]["pid"]):
            return f"ERROR: Process '{name}' is already running. Please stop it first."

    # ⚡ SHIFT-LEFT: Cure the Windows Subprocess Bug
    if sys.platform == "win32":
        if command.startswith("npm "):
            command = command.replace("npm ", "npm.cmd ", 1)
        elif command.startswith("npx "):
            command = command.replace("npx ", "npx.cmd ", 1)

    try:
        # We use posix mapping to ensure Windows backslashes aren't destroyed by shlex
        args = shlex.split(command, posix=(sys.platform != "win32"))
        process = subprocess.Popen(
            args,
            shell=False,
            cwd=safe_cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        state[name] = {"pid": process.pid, "command": command, "cwd": safe_cwd}
        _save_state(state)

        # 🧠 PROPRIOCEPTION: The Health Check
        if port:
            for _ in range(15):  # Poll for 15 seconds
                if is_port_in_use(port):
                    return f"SUCCESS: Process '{name}' started and verified bound to port {port}."
                time.sleep(1)

            # If it failed to bind, slaughter it
            stop_process(name)
            return f"ERROR: Process '{name}' started but failed to bind to port {port} within 15 seconds. It crashed."

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

    if len(state) == 0:
        return "No background processes running."

    return output


def manage_background_process(
    action: str,
    name: str = "",
    command: str = "",
    cwd: str = "",
    port: Optional[int] = None,
) -> str:
    """Tool interface for managing background processes."""
    action = action.lower()
    if action == "start":
        if not command:
            return "ERROR: 'command' required to start."
        proc_name = name if name else command.split()[0]
        return start_process(proc_name, command, cwd, port)
    elif action == "stop":
        if not name and not command:
            return "ERROR: 'name' or 'command' required to stop."
        proc_name = name if name else command.split()[0]
        return stop_process(proc_name)
    elif action == "list":
        return list_processes()
    else:
        return "ERROR: Invalid action. Use 'start', 'stop', or 'list'."
