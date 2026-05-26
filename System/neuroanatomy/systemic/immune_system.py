import os
import re
from typing import Dict, Optional, Tuple, Set
from rich.console import Console

console = Console()

# --- TIER 1: MACROPHAGES (Outbound Stream Scanner) ---
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
        self._keys_to_protect = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY",
            "OPENROUTER_API_KEY",
            "DEPLOYMENT_TOKEN",
            "GATEWAY_BASE_URL",
            "GATEWAY_API_KEY",
        ]
        # ⚡ ZERO DEBT: Track warned mutations to prevent terminal spam
        self._notified_fallbacks: Set[str] = set()

    def secure_environment(self) -> None:
        """Ingests secrets securely without mutating the global host environment."""
        for key in self._keys_to_protect:
            val = os.environ.get(key)
            if val:
                self._secrets[key] = val

    def resolve_routing(self, model: str) -> Tuple[str, Optional[str]]:
        """
        🧠 Thalamic Cross-Modal Routing Waterfall:
        100% Dependable model discovery. Evaluates Gateways, Native Keys, and Fallbacks.
        """
        model_lower = model.lower()
        req_provider = None

        if model_lower.startswith("openai/") or model_lower.startswith("gpt"):
            req_provider = "OPENAI_API_KEY"
        elif model_lower.startswith("anthropic/") or model_lower.startswith("claude"):
            req_provider = "ANTHROPIC_API_KEY"
        elif model_lower.startswith("gemini/"):
            req_provider = "GEMINI_API_KEY"
        elif model_lower.startswith("openrouter/"):
            req_provider = "OPENROUTER_API_KEY"

        # --- 1. GATEWAY BROKER (Absolute Priority) ---
        if "GATEWAY_BASE_URL" in self._secrets:
            return model, self._secrets.get("GATEWAY_API_KEY", "")

        # --- 2. NATIVE PROVIDER MATCH ---
        if req_provider and req_provider in self._secrets:
            return model, self._secrets[req_provider]

        # --- 3. OPENROUTER UNIVERSAL FALLBACK ---
        if "OPENROUTER_API_KEY" in self._secrets:
            routed_model = (
                f"openrouter/{model}"
                if not model_lower.startswith("openrouter/")
                else model
            )
            return routed_model, self._secrets["OPENROUTER_API_KEY"]

        # --- 4. DNA CONFIG GLOBAL DEFAULT ---
        try:
            from System.core.dna import get_dna_config

            global_default = get_dna_config().get("models", {}).get("default")
            if global_default and global_default != model:
                def_model, def_key = self.resolve_routing(global_default)
                if def_key:
                    mutation_key = f"{model}->{def_model}"
                    if mutation_key not in self._notified_fallbacks:
                        console.print(
                            f"\n[bold yellow]⚠️ ROUTING OVERRIDE:[/bold yellow] [dim]Missing keys for '{model}'. Falling back to global default '{def_model}'.[/dim]"
                        )
                        self._notified_fallbacks.add(mutation_key)
                    return def_model, def_key
        except Exception:
            pass

        # --- 5. BEST AVAILABLE NATIVE FALLBACK (System Survival) ---
        fallback_model = None
        fallback_key = None
        if "OPENAI_API_KEY" in self._secrets:
            fallback_model, fallback_key = (
                "openai/gpt-4o-mini",
                self._secrets["OPENAI_API_KEY"],
            )
        elif "ANTHROPIC_API_KEY" in self._secrets:
            fallback_model, fallback_key = (
                "anthropic/claude-3-5-haiku-latest",
                self._secrets["ANTHROPIC_API_KEY"],
            )
        elif "GEMINI_API_KEY" in self._secrets:
            fallback_model, fallback_key = (
                "gemini/gemini-2.5-flash",
                self._secrets["GEMINI_API_KEY"],
            )

        if fallback_model and fallback_key:
            mutation_key = f"{model}->{fallback_model}"
            if mutation_key not in self._notified_fallbacks:
                console.print(
                    f"\n[bold yellow]⚠️ ROUTING OVERRIDE:[/bold yellow] [dim]Missing native credentials for '{model}'. Falling back to '{fallback_model}' to prevent system crash.[/dim]"
                )
                self._notified_fallbacks.add(mutation_key)
            return fallback_model, fallback_key

        # Resolution Failure (Sterile environment / Airgapped)
        return model, None

    def get_api_key_for_model(self, model: str) -> Optional[str]:
        """Legacy interface wrapper for fetching keys without string mutation."""
        _, key = self.resolve_routing(model)
        return key

    def get_secret(self, key: str) -> Optional[str]:
        """Safely retrieve an arbitrary protected secret for an internal organ."""
        return self._secrets.get(key)

    def mask_secrets(self, text: str) -> str:
        """
        🛡️ EFFERENT SHIELD: Scrubs loaded vault secrets from any outbound text stream.
        """
        if not text:
            return text

        scrubbed_text = text
        for key, secret in self._secrets.items():
            if secret and len(secret) > 4:
                scrubbed_text = scrubbed_text.replace(secret, f"[{key}_REDACTED]")

        return scrubbed_text


# The Singleton Vault instance
vault = SecretVault()
