import os
from rich.console import Console

console = Console()


def release_cortisol() -> None:
    """
    Adrenaline Mode (Urgency).
    Bypasses human-in-the-loop safety gates and overrides metabolic exhaustion.
    """
    os.environ["BRAIN_OS_CORTISOL"] = "1"
    os.environ["BRAIN_OS_HEADLESS"] = "1"  # Subconsciously bypasses HITL in tools.py
    console.print(
        "\n[bold red]🩸 Endocrine Release: Cortisol (Adrenaline) active. Safety gates bypassed. Moving fast.[/bold red]"
    )


def release_dopamine() -> None:
    """
    Exploration Mode (Creativity).
    Signals the LLM router to increase temperature and hallucinate novel solutions.
    """
    os.environ["BRAIN_OS_DOPAMINE"] = "1"
    console.print(
        "\n[bold magenta]🩸 Endocrine Release: Dopamine active. Neural temperature increased for exploration.[/bold magenta]"
    )


def is_cortisol_active() -> bool:
    return os.environ.get("BRAIN_OS_CORTISOL") == "1"


def is_dopamine_active() -> bool:
    return os.environ.get("BRAIN_OS_DOPAMINE") == "1"
