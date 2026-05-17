import os
import re
from typing import Dict, Optional
from rich.console import Console

console = Console()

# --- TIER 1: MACROPHAGES (Outbound Stream Scanner) ---
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
    The Immune System (Leukocytes / Macrophages).
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


# --- TIER 2: THE NUCLEAR OPTION (Environment Scrubbing) ---
class SecretVault:
    def __init__(self) -> None:
        self._secrets: Dict[str, str] = {}
        # The specific biological targets we must protect from the Swarm's environment
        self._keys_to_protect = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY",
            "DEPLOYMENT_TOKEN",  # 🔒 SHIFT-LEFT: Generic Deployment Organ Protection
        ]

    def secure_environment(self) -> None:
        """
        The Nuclear Option: Scrubs API keys from the OS environment at boot.
        This guarantees that sub-processes executed by the Swarm cannot access LLM credentials.
        """
        for key in self._keys_to_protect:
            val = os.environ.get(key)
            if val:
                self._secrets[key] = val
                del os.environ[key]  # Erase from the environment

    def get_api_key_for_model(self, model: str) -> Optional[str]:
        """Routes the securely stored key directly to LiteLLM based on the model string."""
        model_lower = model.lower()
        if model_lower.startswith("openai/") or model_lower.startswith("gpt"):
            return self._secrets.get("OPENAI_API_KEY")
        elif model_lower.startswith("anthropic/") or model_lower.startswith("claude"):
            return self._secrets.get("ANTHROPIC_API_KEY")
        elif model_lower.startswith("gemini/"):
            return self._secrets.get("GEMINI_API_KEY")
        return None

    def get_secret(self, key: str) -> Optional[str]:
        """Safely retrieve an arbitrary protected secret for an internal organ."""
        return self._secrets.get(key)

    def mask_secrets(self, text: str) -> str:
        """
        🛡️ EFFERENT SHIELD: Scrubs loaded vault secrets from any outbound text stream.
        Prevents plain-text credential leaks to the console or log files.
        """
        if not text:
            return text

        scrubbed_text = str(text)
        for key, secret in self._secrets.items():
            # Defense in depth: Ignore empty strings or extremely short accidental matches
            if secret and len(secret) > 4:
                scrubbed_text = scrubbed_text.replace(secret, f"[{key}_REDACTED]")

        return scrubbed_text


# The Singleton Vault instance
vault = SecretVault()
