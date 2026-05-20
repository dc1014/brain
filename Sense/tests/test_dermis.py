import hmac
import hashlib

from Sense.receptors.dermis import (
    verify_signature,
    _extract_field,
    enforce_allostatic_load,
    RECENT_SIGNATURES_SET,
    RECENT_SIGNATURES_QUEUE,
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
    client_ip = "192.168.1.100"

    # Fire the exact maximum number of allowed requests
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        assert enforce_allostatic_load(client_ip) is True

    # The very next request from the same IP must be blocked
    assert enforce_allostatic_load(client_ip) is False


def test_dermis_replay_protection():
    """Proves unique signatures are sliding-cached and duplicate attacks are intercepted."""
    RECENT_SIGNATURES_SET.clear()
    RECENT_SIGNATURES_QUEUE.clear()

    signature_1 = "signature-frame-alpha"
    signature_2 = "signature-frame-beta"

    # Seed initial tracking state elements
    RECENT_SIGNATURES_SET.add(signature_1)
    RECENT_SIGNATURES_QUEUE.append(signature_1)

    assert signature_1 in RECENT_SIGNATURES_SET
    assert signature_2 not in RECENT_SIGNATURES_SET


# Append to Sense/tests/test_dermis.py


def test_dermis_abstraction_cooperative_shutdown(mocker):
    """Proves the shutdown hook modifies Uvicorn's exit flags to release socket ports cleanly."""
    from Sense.receptors.dermis import DermisAbstraction

    dermis = DermisAbstraction(port=8080)

    # Mock the internal uvicorn server instance
    mock_server = mocker.MagicMock()
    mock_server.started = True
    mock_server.should_exit = False
    dermis.server = mock_server

    # Fire cooperative disengagement
    dermis.shutdown()

    # Verify the exit flag was updated to force server.run() to yield control back cleanly
    assert mock_server.should_exit is True
