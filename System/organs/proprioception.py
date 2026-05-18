import os
import sys
import json
import signal
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()
STATE_FILE = (
    Path(__file__).parent.parent.parent / "Meta" / "Proprioception" / "motor_state.json"
)


def is_process_alive(pid: int) -> bool:
    """The Necrophage: Cross-platform check to see if a PID is actually alive."""
    if sys.platform == "win32":
        try:
            output = subprocess.check_output(
                f'tasklist /FI "PID eq {pid}" /NH', shell=True, text=True
            )
            return str(pid) in output
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _load_and_heal_state() -> dict:
    """Loads state and autonomously purges any zombie PIDs (processes that crashed)."""
    state = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    healed_state = {}
    zombies_cleared = 0
    for name, info in state.items():
        if is_process_alive(info["pid"]):
            healed_state[name] = info
        else:
            zombies_cleared += 1

    if zombies_cleared > 0:
        _save_state(healed_state)
        console.print(
            f"[dim yellow]🧹 Proprioception: Cleared {zombies_cleared} zombie process(es) from motor state.[/dim yellow]"
        )

    return healed_state


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def start_process(name: str, command: str, cwd: str | None = None) -> str:
    """Spawns a background process safely, blocked by the Amygdala."""
    from System.organs.amygdala import scan_command

    is_safe, threat_reason = scan_command(command)
    if not is_safe:
        console.print(
            f"[bold red]🛑 AMYGDALA BLOCK: Attempted to run forbidden background command: {command}[/bold red]"
        )
        return threat_reason

    state = _load_and_heal_state()
    if name in state:
        return f"PROPRIOCEPTION BLOCK: Process '{name}' is already running (PID {state[name]['pid']}). You MUST stop it before restarting."

    try:
        # SHIFT-LEFT TYPE SAFETY: Explicitly separate the OS calls so Mypy can analyze them
        if sys.platform == "win32":
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # type: ignore
            )
        else:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,  # type: ignore
            )

        import time

        time.sleep(0.5)
        if process.poll() is not None:
            return f"FATAL ERROR: The command '{command}' crashed immediately after starting. Check for syntax errors or port collisions."

        state[name] = {"pid": process.pid, "command": command, "cwd": cwd or "root"}
        _save_state(state)

        console.print(
            f"[dim magenta]🤸 Proprioception: Flexed '{name}' in background (PID {process.pid})[/dim magenta]"
        )
        return f"SUCCESS: Started '{name}' in the background with PID {process.pid}."
    except Exception as e:
        return f"FATAL MOTOR ERROR: Failed to start process: {str(e)}"


def stop_process(name: str) -> str:
    """Relaxes a flexed muscle by killing the background process tree."""
    state = _load_and_heal_state()
    if name not in state:
        return f"PROPRIOCEPTION ERROR: Cannot stop '{name}'. It is not running."

    pid = state[name]["pid"]
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.killpg(os.getpgid(pid), signal.SIGTERM)  # type: ignore
    except Exception as e:
        console.print(f"[dim yellow]Proprioception cleanup notice: {e}[/dim yellow]")

    del state[name]
    _save_state(state)

    console.print(
        f"[dim magenta]🤸 Proprioception: Relaxed '{name}' (Killed PID {pid})[/dim magenta]"
    )
    return f"SUCCESS: Stopped process '{name}' and freed resources."


def list_processes() -> str:
    """Returns spatial awareness of all currently flexed muscles."""
    state = _load_and_heal_state()
    if not state:
        return "No background processes are currently running."

    result = "Running Background Processes:\n"
    for name, info in state.items():
        result += (
            f"- {name} (PID: {info['pid']}): {info['command']} [Dir: {info['cwd']}]\n"
        )
    return result
