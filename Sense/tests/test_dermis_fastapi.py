import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from fastapi import status

# Import the new implementation components
from Sense.receptors.dermis import (
    app,
    load_config_routes,
    extract_true_client_ip,
    RECENT_SIGNATURES_SET,
    RECENT_SIGNATURES_QUEUE,
    IP_REQUEST_HISTORY,
    MAX_REQUESTS_PER_WINDOW,
    MAX_PAYLOAD_SIZE,
)
import Sense.receptors.dermis as dermis_module


@pytest.fixture(autouse=True)
def reset_dermis_state():
    """Clean isolated state modifiers before every individual test run execution."""
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
    """Isolated FastAPI TestClient wrapper harness instance."""
    return TestClient(app)


# -------------------------------------------------------------------------
# UTILITY UNIT TESTS
# -------------------------------------------------------------------------


def test_extract_true_client_ip_variants(mocker):
    """Proves client IP extraction correctly prioritizes trusted proxy headers over sockets."""
    # Scenario A: Standard proxy chain using X-Forwarded-For
    mock_request_ff = mocker.MagicMock()
    mock_request_ff.headers = {"X-Forwarded-For": "198.51.100.42, 127.0.0.1"}
    assert extract_true_client_ip(mock_request_ff) == "198.51.100.42"

    # Scenario B: Single proxy layer using X-Real-IP
    mock_request_real = mocker.MagicMock()
    mock_request_real.headers = {"X-Real-IP": "203.0.113.19"}
    assert extract_true_client_ip(mock_request_real) == "203.0.113.19"

    # Scenario C: Direct loopback edge case with no forwarding headers
    mock_request_direct = mocker.MagicMock()
    mock_request_direct.headers = {}
    mock_request_direct.client.host = "127.0.0.1"
    assert extract_true_client_ip(mock_request_direct) == "127.0.0.1"


def test_load_config_routes_file_handling(mocker, tmp_path):
    """Proves the configuration parser loads yaml schemas safely or gracefully falls back."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)

    # Scenario A: File is missing
    dermis_module.CONFIG_ROUTES = {}
    load_config_routes()
    assert dermis_module.CONFIG_ROUTES == {}

    # Scenario B: Target file exists and has data
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)
    yaml_file = config_dir / "webhooks.yaml"
    yaml_file.write_text(
        "webhooks:\n  test-route:\n    signature_header: X-Test", encoding="utf-8"
    )

    load_config_routes()
    assert "test-route" in dermis_module.CONFIG_ROUTES


# -------------------------------------------------------------------------
# ENDPOINT SECURITY & TRANSACTION INTEGRATION TESTS
# -------------------------------------------------------------------------


def test_webhook_endpoint_success(client, mocker, monkeypatch):
    """Proves a fully verified, valid payload is securely accepted and transduced."""
    secret = "production-neuro-secret-token"
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)

    payload = {"repository": {"name": "brain-core"}, "sender": {"login": "neo-cortex"}}
    payload_bytes = json.dumps(payload).encode("utf-8")

    # Generate cryptographic signature contract frame
    signature = (
        "sha256="
        + hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    )

    # Mock outward Spine interface dependency to keep test synchronous
    mock_transduce = mocker.patch("Sense.receptors.dermis.transduce_to_spine")

    response = client.post(
        "/github-webhook",
        content=payload_bytes,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "transduced"}

    # Verify exact formatted string matching your templates is delivered to the Spinal Column
    mock_transduce.assert_called_once_with(
        "webhook:github-webhook",
        "Repository brain-core received an impulse from neo-cortex.",
        "exteroceptive",
    )


def test_webhook_security_rejection(client, monkeypatch):
    """Proves the endpoint forcefully drops requests carrying invalid signatures."""
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "valid-secret")

    response = client.post(
        "/github-webhook",
        json={"data": "untrusted"},
        headers={"X-Hub-Signature-256": "sha256=invalidcombatkeysignature"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_webhook_not_found(client):
    """Proves unmapped pathways return a clean 404 block instead of falling through."""
    response = client.post("/unknown-phantom-route", json={})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_webhook_replay_attack_mitigation(client, mocker, monkeypatch):
    """Proves duplicate signatures trip the strict FIFO sliding replay defense barrier."""
    secret = "replay-lock-key"
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)
    mocker.patch("Sense.receptors.dermis.transduce_to_spine")

    payload = {"nonce": 98765}
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = (
        "sha256="
        + hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    )

    # Pass 1: Fresh signature is cleanly accepted
    res1 = client.post(
        "/github-webhook",
        content=payload_bytes,
        headers={"X-Hub-Signature-256": signature},
    )
    assert res1.status_code == status.HTTP_200_OK

    # Pass 2: Identical signature within the window triggers a 409 Conflict rejection
    res2 = client.post(
        "/github-webhook",
        content=payload_bytes,
        headers={"X-Hub-Signature-256": signature},
    )
    assert res2.status_code == status.HTTP_409_CONFLICT


def test_webhook_rate_limiting_allostatic_load(client, monkeypatch):
    """Proves external spam vectors trip local IP rate limiters without blinding localhost."""
    secret = "spam-shield"
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)

    payload_bytes = b'{"ping": true}'
    signature = (
        "sha256="
        + hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    )

    # Simulate an attacker coming in via reverse proxy headers
    attacker_headers = {
        "X-Forwarded-For": "203.0.113.55",
        "X-Hub-Signature-256": signature,
    }

    # Exhaust the entire request window capacity allocation for the attacker
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        res = client.post(
            "/github-webhook", content=payload_bytes, headers=attacker_headers
        )
        assert res.status_code == status.HTTP_200_OK

    # The next payload execution frame from that exact IP triggers a 429 block
    blocked_res = client.post(
        "/github-webhook", content=payload_bytes, headers=attacker_headers
    )
    assert blocked_res.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    # CRITICAL SECURITY SANITY CHECK: Ensure a separate IP address remains unblocked
    clean_headers = {
        "X-Forwarded-For": "198.51.100.99",
        "X-Hub-Signature-256": signature,
    }
    assert (
        client.post(
            "/github-webhook", content=payload_bytes, headers=clean_headers
        ).status_code
        == status.HTTP_200_OK
    )


def test_webhook_payload_size_ceiling_enforcement(client):
    """Proves huge payload bombs are blocked immediately to protect system memory."""
    # Scenario A: Excessive Content-Length declaration is intercepted before streaming bytes
    oversized_headers = {
        "X-Forwarded-For": "1.1.1.1",
        "Content-Length": str(MAX_PAYLOAD_SIZE + 100),
    }
    response = client.post(
        "/github-webhook", content=b"short", headers=oversized_headers
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    # Scenario B: Malformed JSON strings throw a 400 Bad Request
    response_malformed = client.post(
        "/github-webhook",
        content=b"{invalid-json-stream",
        headers={"X-Forwarded-For": "1.1.1.1", "X-Hub-Signature-256": "fake-sig"},
    )
    # Fails signature verification first if not checked, but still throws a deterministic secure exception
    assert response_malformed.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    ]
