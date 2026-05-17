import json
import subprocess
import shlex
import atexit
import socket
import time
import sys
import os
from typing import Optional, Generator
from contextlib import contextmanager
from pathlib import Path
from rich.console import Console

# ⚡ ZERO-DEBT: Import our native dual-protocol lock
from System.core.locks import BiologicalLock

console = Console()
STATE_FILE = (
    Path(__file__).parent.parent.parent / "Meta" / "Proprioception" / "motor_state.json"
)


def _load_state() -> dict:
    """Isolated state load wrapper (Failsafe fallback)."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@contextmanager
def mutate_state() -> Generator[dict, None, None]:
    """
    🛡️ SHIFT-LEFT SECURITY: Atomic Context Manager.
    Locks the state file continuously across the entire Read-Modify-Write lifecycle
    to completely eliminate multi-agent race conditions under Swarm execution.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with BiologicalLock(str(STATE_FILE)):
        # 1. Read the baseline state while holding the lock
        state = _load_state()

        try:
            # 2. Yield control to let the tool layer modify the entries
            yield state
        finally:
            # 3. Write back the finalized mutation before releasing the lock
            try:
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2)
            except Exception as e:
                console.print(
                    f"[bold red]🧠 Proprioception Sync Error: Failed to commit state disk sync: {e}[/bold red]"
                )


def sweep_zombies() -> None:
    """Kills tracked processes tied to this session, or orphaned by an OS hard crash."""
    import psutil

    # ⚡ ZERO-DEBT: Use atomic context manager to ensure safe deletions
    with mutate_state() as state:
        if not state:
            return

        current_pid = os.getpid()
        killed_count = 0
        keys_to_delete = []

        for name, info in list(state.items()):
            pid = info.get("pid")
            parent_pid = info.get("parent_pid")

            if not pid:
                keys_to_delete.append(name)
                continue

            is_ours = parent_pid == current_pid
            is_orphan = False

            if parent_pid and parent_pid != current_pid:
                if not psutil.pid_exists(parent_pid):
                    is_orphan = True

            if is_ours or is_orphan:
                try:
                    if psutil.pid_exists(pid):
                        parent = psutil.Process(pid)
                        for child in parent.children(recursive=True):
                            child.kill()
                        parent.kill()
                        killed_count += 1
                except Exception:
                    pass
                keys_to_delete.append(name)

        if killed_count > 0:
            print(
                f"\n🧠 Proprioception: Swept {killed_count} background processes (Session end / Orphan cleanup)."
            )

        for k in keys_to_delete:
            state.pop(k, None)


# Bind the death sweep to the graceful OS lifecycle
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

    is_safe_command, reason = scan_command(command)
    if not is_safe_command:
        return reason

    target_cwd = cwd if cwd else str(ROOT_DIR / "Studio")
    is_safe_path, safe_cwd = validate_execution_path(target_cwd)
    if not is_safe_path:
        return safe_cwd

    sweep_zombies()

    # ⚡ ZERO-DEBT: Wrap process assignment inside atomic state mutations
    with mutate_state() as state:
        if name in state:
            if psutil.pid_exists(state[name]["pid"]):
                return (
                    f"ERROR: Process '{name}' is already running. Please stop it first."
                )

        if sys.platform == "win32":
            if command.startswith("npm "):
                command = command.replace("npm ", "npm.cmd ", 1)
            elif command.startswith("npx "):
                command = command.replace("npx ", "npx.cmd ", 1)

        try:
            env_dict = os.environ.copy()
            args = shlex.split(command, posix=(sys.platform != "win32"))
            process = subprocess.Popen(
                args,
                shell=False,
                cwd=safe_cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env_dict,
            )

            state[name] = {
                "pid": process.pid,
                "command": command,
                "cwd": safe_cwd,
                "parent_pid": os.getpid(),
            }
        except Exception as e:
            return f"EXECUTION ERROR: {str(e)}"

    # 🧠 PROPRIOCEPTION: The Health Check (Executed outside the lock to prevent hanging other threads)
    if port:
        for _ in range(15):
            if is_port_in_use(port):
                return f"SUCCESS: Process '{name}' started and verified bound to port {port}."
            time.sleep(1)

        stop_process(name)
        return f"ERROR: Process '{name}' started but failed to bind to port {port} within 15 seconds. It crashed."

    # ⚡ ZERO-DEBT: Safe dynamic property extraction on native Popen instance
    return f"SUCCESS: Process '{name}' started with PID {process.pid if 'process' in locals() else 'unknown'} in {safe_cwd}."


def stop_process(name: str) -> str:
    """Stops a background process safely."""
    import psutil

    # ⚡ ZERO-DEBT: Wrap deletion inside atomic context
    with mutate_state() as state:
        if name not in state:
            return f"ERROR: Process '{name}' not found in state."

        pid = state[name]["pid"]
        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            del state[name]
            return f"SUCCESS: Process '{name}' (PID {pid}) stopped."
        except psutil.NoSuchProcess:
            del state[name]
            return f"SUCCESS: Process '{name}' was already dead. State cleaned."
        except Exception as e:
            return f"ERROR stopping process: {str(e)}"


def list_processes() -> str:
    """Lists running background processes safely."""
    import psutil

    # ⚡ ZERO-DEBT: Safe isolated state read
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
        with mutate_state() as locked_state:
            for d in dead_procs:
                locked_state.pop(d, None)
        output += f"\n(Cleaned up {len(dead_procs)} dead processes)"

    # Double check active constraints
    updated_state = _load_state()
    if len(updated_state) == 0:
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
