# --- System/tests/core/test_onboarding_security.py ---
from pathlib import Path
from System.core.onboarding.security import (
    is_valid_key_format,
    _atomic_write_text,
    verify_deno_sandbox,
)


def test_atomic_write_text(tmp_path: Path):
    """Proves the atomic writer creates a temporary file and successfully swaps it."""
    target_file = tmp_path / ".env"
    content = "GEMINI_API_KEY=AIzaSyTest"

    _atomic_write_text(target_file, content)

    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == content
    assert not target_file.with_suffix(".tmp").exists()


def test_is_valid_key_format():
    """Proves strict regex enforcement against malformed API keys."""
    # Gemini
    assert is_valid_key_format("GEMINI", "AIzaSy" + ("A" * 33))
    assert not is_valid_key_format("GEMINI", "invalid_key_string")

    # Anthropic
    assert is_valid_key_format("ANTHROPIC", "sk-ant-" + ("B" * 95))
    assert not is_valid_key_format("ANTHROPIC", "sk-ant-short")

    # OpenAI
    assert is_valid_key_format("OPENAI", "sk-" + ("C" * 48))
    assert is_valid_key_format("OPENAI", "sk-proj-" + ("D" * 20))

    # Empty or unknown
    assert not is_valid_key_format("OPENAI", "")
    assert not is_valid_key_format("UNKNOWN_PROV", "some_key")


def test_verify_deno_sandbox(mocker):
    """Proves the sandbox verification correctly identifies the Deno binary."""
    mocker.patch(
        "System.core.onboarding.security.shutil.which", return_value="/usr/bin/deno"
    )
    assert verify_deno_sandbox()

    mocker.patch("System.core.onboarding.security.shutil.which", return_value=None)
    assert not verify_deno_sandbox()
