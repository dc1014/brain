import os
import re
from typing import Dict, Optional, Tuple
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
# --- Replacing SecretVault inside System/neuroanatomy/systemic/immune_system.py ---


# --- In System/neuroanatomy/systemic/immune_system.py ---
class SecretVault:
    def __init__(self) -> None:
        self._secrets: Dict[str, str] = {}
        # The specific biological targets we must protect from the Swarm's environment
        self._keys_to_protect = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY",
            "OPENROUTER_API_KEY",
            "DEPLOYMENT_TOKEN",
            "GATEWAY_BASE_URL",
            "GATEWAY_API_KEY",
        ]

    def secure_environment(self) -> None:
        """Ingests secrets securely without mutating the global host environment."""
        for key in self._keys_to_protect:
            val = os.environ.get(key)
            if val:
                self._secrets[key] = val

    def resolve_routing(self, model: str) -> Tuple[str, Optional[str]]:
        """
        🧠 Thalamic Cross-Modal Routing:
        Auto-discovers available keys and dynamically mutates the model string and key assignment.
        1. Native Key Match
        2. OpenRouter Aggregation Fallback
        3. User-Configured Global Default Model Fallback (DNA Config)
        4. Single-Key Universal Auto-Discovery Fallback
        5. Absolute Hardcoded Failsafe Fallback
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

        # 1. Native Provider Match
        if req_provider and req_provider in self._secrets:
            return model, self._secrets[req_provider]

        # 2. OpenRouter Fallback Mutation
        if "OPENROUTER_API_KEY" in self._secrets:
            # Litellm needs the 'openrouter/' prefix to route aggregator keys correctly
            routed_model = (
                f"openrouter/{model}"
                if not model_lower.startswith("openrouter/")
                else model
            )
            return routed_model, self._secrets["OPENROUTER_API_KEY"]

        # 3. User-Configured Global Default Model Fallback (Defends against Circular Boot Cycles)
        try:
            from System.core.dna import get_dna_config

            global_default = get_dna_config().get("models", {}).get("default")
            if global_default and global_default != model:
                def_model, def_key = self.resolve_routing(global_default)
                if def_key:
                    return def_model, def_key
        except Exception:
            pass  # Suppress circular drift if core paths are loading synchronously

        # 4. Single-Key Universal Fallback (Auto-discovery match for single-key setups)
        available_providers = [
            k
            for k in self._secrets.keys()
            if k.endswith("_API_KEY") and k != "OPENROUTER_API_KEY"
        ]
        if len(available_providers) == 1:
            sole_provider = available_providers[0]
            if sole_provider == "GEMINI_API_KEY":
                return "gemini/gemini-2.5-flash", self._secrets[sole_provider]
            elif sole_provider == "OPENAI_API_KEY":
                return "openai/gpt-4o-mini", self._secrets[sole_provider]
            elif sole_provider == "ANTHROPIC_API_KEY":
                return "anthropic/claude-3-haiku-20240307", self._secrets[sole_provider]

        # 5. Absolute Hardcoded Failsafe Fallback (If all matching channels are de-innervated)
        # Check if ANY key is available to execute a generic, desperate routing save
        for provider_key, secret_val in self._secrets.items():
            if provider_key.endswith("_API_KEY") and secret_val:
                if provider_key == "GEMINI_API_KEY":
                    return "gemini/gemini-2.5-flash", secret_val
                elif provider_key == "OPENAI_API_KEY":
                    return "openai/gpt-4o-mini", secret_val
                elif provider_key == "ANTHROPIC_API_KEY":
                    return "anthropic/claude-3-haiku-20240307", secret_val

        # Resolution Failure (Completely sterile environment)
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
        Prevents plain-text credential leaks to the console or log files.
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
