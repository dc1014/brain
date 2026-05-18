from System.organs.immune_system import scan_for_pathogens


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
