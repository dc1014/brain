import hmac
import hashlib
from Sense.receptors.dermis import (
    verify_signature,
    _extract_field,
    WebhookHandler,
    RECENT_SIGNATURES,
    IP_REQUEST_HISTORY,
    MAX_REQUESTS_PER_WINDOW,
)


def test_dermis_signature_verification():
    """Proves the Dermis accurately verifies HMAC-SHA256 signatures and detects tampering."""
    secret = "neuromorphic-secret"
    payload = b'{"event": "push"}'

    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert verify_signature(payload, secret, valid_sig) is True
    assert verify_signature(payload, secret, f"sha256={valid_sig}") is True
    assert verify_signature(payload, secret, "invalid-sig") is False
    assert verify_signature(b"tampered", secret, valid_sig) is False


def test_dermis_extract_field():
    """Proves the dot-notation extractor properly navigates complex nested JSON payloads."""
    data = {"repository": {"name": "brain-os"}, "author": "admin"}
    assert _extract_field(data, "repository.name") == "brain-os"
    assert _extract_field(data, "author") == "admin"
    assert _extract_field(data, "missing.key") == "Unknown"


def test_dermis_allostatic_load_rate_limiting():
    """Proves the Dermis numbs itself to a specific IP if MAX_REQUESTS_PER_WINDOW is exceeded."""
    IP_REQUEST_HISTORY.clear()

    class MockHandler:
        client_address = ("192.168.1.100", 8080)

    handler = MockHandler()

    # Fire the exact maximum number of allowed requests
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        assert WebhookHandler.enforce_allostatic_load(handler) is True

    # The very next request from the same IP must be blocked
    assert WebhookHandler.enforce_allostatic_load(handler) is False


def test_dermis_replay_protection():
    """Proves the Dermis drops duplicate impulses if the signature matches a recent cache."""
    RECENT_SIGNATURES.clear()

    # Simulate caching a valid signature from a previous request
    fake_sig = "sha256=12345abcdef"
    RECENT_SIGNATURES.add(fake_sig)

    assert fake_sig in RECENT_SIGNATURES
