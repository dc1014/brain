import os
from System.neuroanatomy.systemic.immune_system import scan_for_pathogens, SecretVault


def test_scan_for_pathogens():
    # Clean text
    safe, msg = scan_for_pathogens("Just a normal log message.")
    assert safe is True

    # Detected AWS
    safe, msg = scan_for_pathogens("Here is my AKIAIOSFODNN7EXAMPLE key.")
    assert safe is False
    assert "AWS Access Key" in msg

    # Detected OpenAI
    safe, msg = scan_for_pathogens("My key: sk-proj-1234567890abcdef1234567890abcdef")
    assert safe is False
    assert "OpenAI API Key" in msg


def test_secret_vault_secure_environment(mocker):
    mocker.patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "sk-12345",
            "DEPLOYMENT_TOKEN": "deploy-token-xyz",
            "OTHER_VAR": "keep-me",
        },
        clear=True,
    )

    vault = SecretVault()
    vault.secure_environment()

    # The vault should ingest the keys safely into internal memory storage
    assert vault.get_secret("OPENAI_API_KEY") == "sk-12345"
    assert vault.get_secret("DEPLOYMENT_TOKEN") == "deploy-token-xyz"

    # Thread Safety Check: Confirm host environment state remains unmutated at runtime
    assert "OPENAI_API_KEY" in os.environ
    assert os.environ["OTHER_VAR"] == "keep-me"

    assert vault.get_secret("OPENAI_API_KEY") == "sk-12345"


def test_secret_vault_resolve_routing_native(mocker):
    mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-12345"}, clear=True)
    vault = SecretVault()
    vault.secure_environment()

    model, key = vault.resolve_routing("openai/gpt-4o")
    assert model == "openai/gpt-4o"
    assert key == "sk-12345"


def test_secret_vault_resolve_routing_openrouter_fallback(mocker):
    mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-12345"}, clear=True)
    vault = SecretVault()
    vault.secure_environment()

    # Native key missing, route dynamically through OpenRouter
    model, key = vault.resolve_routing("anthropic/claude-3-haiku")
    assert model == "openrouter/anthropic/claude-3-haiku"
    assert key == "or-12345"


def test_secret_vault_resolve_routing_single_key_fallback(mocker):
    mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-12345"}, clear=True)
    vault = SecretVault()
    vault.secure_environment()

    # User asks for Anthropic, but only installed Gemini. Brain auto-adjusts.
    model, key = vault.resolve_routing("anthropic/claude-3-haiku")
    assert model == "gemini/gemini-2.5-flash"
    assert key == "gemini-12345"


def test_secret_vault_mask_secrets(mocker):
    mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-secret-key-123"}, clear=True)
    vault = SecretVault()
    vault.secure_environment()

    text = "Connecting with sk-secret-key-123 now."
    masked = vault.mask_secrets(text)
    assert "sk-secret-key-123" not in masked
    assert "[OPENAI_API_KEY_REDACTED]" in masked


def test_secret_vault_resolve_routing_user_configured_global_default(mocker):
    """Proves that if an explicit default model configuration exists, the vault securely falls back to it."""
    mocker.patch.dict(
        os.environ, {"OPENAI_API_KEY": "sk-default-testing-123"}, clear=True
    )
    mocker.patch(
        "System.core.dna.get_dna_config",
        return_value={"models": {"default": "openai/gpt-4o-mini"}},
    )

    vault = SecretVault()
    vault.secure_environment()

    model, key = vault.resolve_routing("anthropic/claude-3-5-sonnet")
    assert model == "openai/gpt-4o-mini"
    assert key == "sk-default-testing-123"


def test_secret_vault_resolve_routing_absolute_failsafe(mocker):
    """Proves that if DNA config fails/is missing, the vault falls back to any live key as an absolute failsafe."""
    mocker.patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "claude-failsafe-secret"}, clear=True
    )
    # Simulate a circular import exception or empty dictionary when calling DNA config
    mocker.patch(
        "System.core.dna.get_dna_config",
        side_effect=Exception("Circular Import Deadlock"),
    )

    vault = SecretVault()
    vault.secure_environment()

    # Request an unrelated model while config is down. The failsafe should save the routing.
    model, key = vault.resolve_routing("openai/gpt-4o")
    assert model == "anthropic/claude-3-haiku-20240307"
    assert key == "claude-failsafe-secret"
