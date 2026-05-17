import os
from System.neuroanatomy.systemic.immune_system import scan_for_pathogens, SecretVault

# --- Original Macrophage Tests ---


def test_immune_system_allows_safe_code():
    is_clean, msg = scan_for_pathogens("def connect_db():\n    return 'connected'")
    assert is_clean is True
    assert msg == ""


def test_immune_system_blocks_aws_keys():
    is_clean, msg = scan_for_pathogens("const aws_key = 'AKIAIOSFODNN7EXAMPLE';")
    assert is_clean is False
    assert "AWS Access Key" in msg


def test_immune_system_blocks_openai_keys():
    is_clean, msg = scan_for_pathogens(
        "client = OpenAI(api_key='sk-proj-1234567890abcdef1234567890abcdef')"
    )
    assert is_clean is False
    assert "OpenAI API Key" in msg


def test_immune_system_blocks_private_keys():
    private_key_mock = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA..."
    is_clean, msg = scan_for_pathogens(private_key_mock)
    assert is_clean is False
    assert "RSA Private Key" in msg


# --- New Nuclear Option Test ---


def test_nuclear_option_scrubbing(monkeypatch):
    # 1. Simulate the .env loading process
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake123")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    monkeypatch.setenv("SAFE_VAR", "visible")

    # 2. Engage the Immune System
    vault = SecretVault()
    vault.secure_environment()

    # 3. PROVE THE ENVIRONMENT IS MATHEMATICALLY SCRUBBED
    assert "OPENAI_API_KEY" not in os.environ
    assert "ANTHROPIC_API_KEY" not in os.environ
    assert os.environ.get("SAFE_VAR") == "visible"  # Harmless vars survive

    # 4. Prove the Vault safely retained the keys in memory
    assert vault.get_api_key_for_model("openai/gpt-4o") == "sk-fake123"
    assert vault.get_api_key_for_model("anthropic/claude-3-5-sonnet") == "sk-ant-fake"


def test_efferent_shield_secret_masking(monkeypatch):
    """Proves the vault completely redacts active secrets from outbound text streams."""
    # 1. Simulate the .env loading process with mock secrets
    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-super-secret-12345")
    monkeypatch.setenv("DEPLOYMENT_TOKEN", "vercel_deploy_999")

    # 2. Engage the Immune System Vault
    vault = SecretVault()
    vault.secure_environment()

    # 3. Simulate an LLM accidentally leaking secrets in a response
    raw_output = (
        "Here is the key: sk-proj-super-secret-12345 and token vercel_deploy_999."
    )

    # 4. Pass through the Efferent Shield
    safe_output = vault.mask_secrets(raw_output)

    # 5. Strict Validation
    assert "sk-proj-super-secret-12345" not in safe_output
    assert "vercel_deploy_999" not in safe_output
    assert "[OPENAI_API_KEY_REDACTED]" in safe_output
    assert "[DEPLOYMENT_TOKEN_REDACTED]" in safe_output
