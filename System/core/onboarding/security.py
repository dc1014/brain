# --- System/core/onboarding/security.py ---
import shutil
import re
from pathlib import Path
from typing import Dict

# Strict Regex patterns to catch malformed keys before network requests
KEY_PATTERNS: Dict[str, str] = {
    "OPENAI_API_KEY": r"^(sk-[a-zA-Z0-9]{48}|sk-proj-[a-zA-Z0-9_-]+)$",
    "ANTHROPIC_API_KEY": r"^sk-ant-[a-zA-Z0-9_-]{95,}$",
    "GEMINI_API_KEY": r"^AIzaSy[a-zA-Z0-9_-]{33}$",
    "OPENROUTER_API_KEY": r"^sk-or-v1-[a-zA-Z0-9_-]{64}$",
}


def is_valid_key_format(provider: str, api_key: str) -> bool:
    """Validates the raw string format of an API key against known provider patterns."""
    if not api_key:
        return False
    pattern = KEY_PATTERNS.get(f"{provider.upper()}_API_KEY")
    if not pattern:
        return False
    return bool(re.match(pattern, api_key))


def _atomic_write_text(target_path: Path, text_content: str) -> None:
    """
    Safely writes text to a file.
    SHIFT-LEFT: Automatically backs up the existing file to .bak to prevent data loss.
    """
    if target_path.exists():
        backup_path = target_path.with_suffix(target_path.suffix + ".bak")
        shutil.copy(str(target_path), str(backup_path))

    tmp_path = target_path.with_suffix(".tmp")
    tmp_path.write_text(text_content, encoding="utf-8")
    shutil.move(str(tmp_path), str(target_path))


def verify_deno_sandbox() -> bool:
    """Verifies the host machine has the Deno WASM engine required for sandboxed execution."""
    return shutil.which("deno") is not None
