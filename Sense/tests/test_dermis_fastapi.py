import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient

from Sense.receptors.dermis import (
    app,
    RECENT_SIGNATURES_SET,
    RECENT_SIGNATURES_QUEUE,
    IP_REQUEST_HISTORY,
    MAX_REQUESTS_PER_WINDOW,
    MAX_PAYLOAD_SIZE,
)
import Sense.receptors.dermis as dermis_module


def generate_signature(payload_bytes: bytes) -> str:
    secret = b"my_super_secret"
    return "sha256=" + hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def reset_dermis_state(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "my_super_secret")
    RECENT_SIGNATURES_SET.clear()
    RECENT_SIGNATURES_QUEUE.clear()
    IP_REQUEST_HISTORY.clear()
    dermis_module.CONFIG_ROUTES = {
        "github-webhook": {
            "signature_header": "X-Hub-Signature-256",
            "secret_env_var": "GITHUB_WEBHOOK_SECRET",
            "target_action": "exteroceptive",
            "payload_mapping": {
                "repo_name": "repository.name",
                "sender": "sender.login",
            },
            "template": "Repository {repo_name} received an impulse from {sender}.",
        }
    }
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_webhook_payload_size_ceiling_enforcement(client):
    oversized_headers = {
        "X-Forwarded-For": "1.1.1.1",
        "Content-Length": str(MAX_PAYLOAD_SIZE + 100),
    }
    response = client.post(
        "/github-webhook", content=b"short", headers=oversized_headers
    )
    assert response.status_code == 413

    # ⚡ FIX: Use a valid signature for the malformed body so it passes Auth and hits the JSON parser!
    malformed_body = b"{invalid-json-stream"
    valid_sig = generate_signature(malformed_body)
    response_malformed = client.post(
        "/github-webhook",
        content=malformed_body,
        headers={"X-Forwarded-For": "1.1.1.1", "X-Hub-Signature-256": valid_sig},
    )
    assert response_malformed.status_code == 400


def test_load_config_routes_file_handling():
    assert isinstance(dermis_module.CONFIG_ROUTES, dict)


def test_webhook_rate_limiting_allostatic_load(client):
    """Proves the Dermis layer effectively prevents DoS API flooding."""
    # Spam the endpoint up to the exact limit
    for i in range(MAX_REQUESTS_PER_WINDOW):
        # ⚡ FIX: Make payload unique to avoid 409 Replay Attack rejection during the loop!
        payload_bytes = f'{{"repository": {{"name": "test"}}, "sender": {{"login": "attacker{i}"}}}}'.encode()
        signature = generate_signature(payload_bytes)
        headers = {
            "X-Forwarded-For": "203.0.113.99",
            "X-Hub-Signature-256": signature,
        }
        response = client.post(
            "/github-webhook", content=payload_bytes, headers=headers
        )
        assert response.status_code == 200

    # ⚡ FIX: The very next request must trigger the 429 Too Many Requests rejection
    payload_bytes = (
        b'{"repository": {"name": "test"}, "sender": {"login": "attacker_final"}}'
    )
    signature = generate_signature(payload_bytes)

    headers_final = {
        "X-Forwarded-For": "203.0.113.99",
        "X-Hub-Signature-256": signature,
    }

    response = client.post(
        "/github-webhook", content=payload_bytes, headers=headers_final
    )
    assert response.status_code == 429
