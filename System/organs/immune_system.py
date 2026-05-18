import re
from rich.console import Console

console = Console()

# Known pathogen signatures (Zero-Debt Regex for high-risk secrets)
PATHOGENS = {
    "AWS Access Key": r"\b(AKIA[0-9A-Z]{16})\b",
    "OpenAI API Key": r"\b(sk-[a-zA-Z0-9]{48}|sk-proj-[a-zA-Z0-9_-]+)\b",
    "Stripe Secret Key": r"\b(sk_(live|test)_[0-9a-zA-Z]{24,})\b",
    "GitHub Token": r"\b(gh[p|a|s|r]_[a-zA-Z0-9]{36})\b",
    "RSA Private Key": r"-----BEGIN (RSA|OPENSSH) PRIVATE KEY-----",
}


def scan_for_pathogens(content: str) -> tuple[bool, str]:
    """
    The Immune System (Leukocytes).
    Scans outbound text streams for leaked secrets before they are written to disk.
    """
    for pathogen_name, pattern in PATHOGENS.items():
        if re.search(pattern, content):
            console.print(
                f"\n[bold red]🦠 IMMUNE RESPONSE TRIGGERED: Detected {pathogen_name} in outbound data stream![/bold red]"
            )
            return (
                False,
                f"SECURITY BLOCK (Immune System): Attempted to write a raw {pathogen_name} to disk. You must use environment variables (.env) instead of hardcoding secrets.",
            )

    return True, ""
