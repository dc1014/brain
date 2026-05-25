import json
import subprocess
import datetime
import shlex
from pathlib import Path
from rich.console import Console

console = Console()
HABITS_FILE = (
    Path(__file__).parent.parent.parent / "Meta" / "Basal_Ganglia" / "habits.json"
)


def _load_habits() -> dict:
    if HABITS_FILE.exists():
        try:
            with open(HABITS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_habits(habits: dict) -> None:
    HABITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HABITS_FILE, "w", encoding="utf-8") as f:
        json.dump(habits, f, indent=2)


def form_habit(name: str, command: str, interval_minutes: int) -> str:
    """
    Basal Ganglia: Forms a new subconscious habit (cron job).
    The command will run automatically every X minutes.
    """
    # SHIFT-LEFT SECURITY: Route through Amygdala before saving the habit
    from System.neuroanatomy.limbic.amygdala import scan_command

    is_safe, threat_reason = scan_command(command)
    if not is_safe:
        return f"AMYGDALA BLOCK: Refusing to form habit. {threat_reason}"

    habits = _load_habits()
    habits[name] = {
        "command": command,
        "interval_minutes": interval_minutes,
        "last_run": "1970-01-01T00:00:00",  # Force an immediate run on next tick
    }
    _save_habits(habits)
    console.print(
        f"[bold magenta] Basal Ganglia: Formed new habit '{name}' (every {interval_minutes}m)[/bold magenta]"
    )
    return f"SUCCESS: Habit '{name}' formed."


def break_habit(name: str) -> str:
    """Deletes a habit."""
    habits = _load_habits()
    if name in habits:
        del habits[name]
        _save_habits(habits)
        return f"SUCCESS: Habit '{name}' broken."
    return f"ERROR: Habit '{name}' does not exist."


def tick_habits() -> None:
    """
    The Subconscious Pulse.
    Checks all habits and executes them in the background, logging output for transparency.
    """
    habits = _load_habits()
    now = datetime.datetime.now(datetime.timezone.utc)
    updated = False

    # GLASS BRAIN: Log background execution so failures aren't invisible
    log_file_path = HABITS_FILE.parent / "habit_logs.md"

    for name, data in habits.items():
        try:
            last_run = datetime.datetime.fromisoformat(data["last_run"])
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=datetime.timezone.utc)

            delta = now - last_run

            if delta.total_seconds() >= (data["interval_minutes"] * 60):
                console.print(
                    f"[dim magenta] Basal Ganglia: Triggering habit '{name}'...[/dim magenta]"
                )

                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"\n### Executed '{name}' at {now.isoformat()}\n")
                    log_file.write(f"**Command:** `{data['command']}`\n```text\n")
                    log_file.flush()

                    # SHIFT-LEFT: Sandbox Enforcement for Background Habits
                    from System.neuroanatomy.systemic.blood_brain_barrier import (
                        validate_execution_path,
                    )
                    from System.core.paths import ROOT_DIR

                    # SHIFT-LEFT: Sandbox Enforcement for Background Habits

                    # FIX: Default to Studio, because ROOT_DIR is blocked by the BBB
                    is_safe, safe_cwd = validate_execution_path(
                        str(ROOT_DIR / "Studio")
                    )

                    if is_safe:
                        # SHIFT-LEFT: Strip shell=True, parse arguments safely
                        args = shlex.split(data["command"])
                        subprocess.Popen(
                            args,
                            shell=False,
                            cwd=safe_cwd,
                            stdout=log_file,
                            stderr=subprocess.STDOUT,
                        )
                    else:
                        log_file.write(
                            f"\n[BLOCKED] Habit execution aborted. Invalid Sandbox: {safe_cwd}\n"
                        )

                habits[name]["last_run"] = now.isoformat()
                updated = True
        except Exception as e:
            console.print(f"[dim red]Basal Ganglia Error on '{name}': {e}[/dim red]")

    if updated:
        _save_habits(habits)
