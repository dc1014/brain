import os
import re
from rich.console import Console

console = Console()


def inspect_toxins(command: str) -> tuple[bool, str]:
    """
    The Blood-Brain Barrier.
    Prevents the autonomous installation of external packages during headless/dream states
    to protect against supply-chain poisoning and remote code execution.
    """
    # If a human is actively at the keyboard (not headless), the BBB lets the human decide.
    if os.environ.get("BRAIN_OS_HEADLESS") != "1":
        return True, ""

    # List of toxic patterns that reach out to the internet to download and execute code
    toxin_patterns = [
        r"\bnpm\s+(i|install|add)\b",
        r"\byarn\s+(add)\b",
        r"\bpnpm\s+(add|install)\b",
        r"\bpip\s+install\b",
        r"\buv\s+(add|pip\s+install)\b",
        r"\bbrew\s+install\b",
        r"\bapt(-get)?\s+install\b",
        r"\bcurl\b.*\|.*\b(bash|sh)\b",  # Curl-to-bash scripts
        r"\bwget\b.*\|.*\b(bash|sh)\b",
    ]

    for pattern in toxin_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            console.print(
                "\n[bold red]🛑 Blood-Brain Barrier Triggered: Blocked toxic network command during REM sleep.[/bold red]"
            )
            console.print(f"[dim]Command intercepted: {command}[/dim]")
            return (
                False,
                "SECURITY BLOCK (Blood-Brain Barrier): Autonomous package installation is strictly forbidden during REM sleep to prevent supply-chain attacks. Dream with the packages you already have.",
            )

    return True, ""
