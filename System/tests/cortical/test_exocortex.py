import json
import hashlib
from System.neuroanatomy.cortical.exocortex import Exocortex


def test_exocortex_rejects_missing_keys(tmp_path, monkeypatch):
    """Proves the Exocortex blocks payloads if the cryptographic membrane is unconfigured."""
    monkeypatch.setattr("System.neuroanatomy.cortical.exocortex.ROOT_DIR", tmp_path)

    exo = Exocortex()
    response = exo.process_inbound_pulse("node_1", '{"action": "READ"}', "fake_sig")
    assert "403" in response


def test_exocortex_rejects_invalid_signature(tmp_path, monkeypatch):
    """Proves Shift-Left security by blocking altered payloads."""
    monkeypatch.setattr("System.neuroanatomy.cortical.exocortex.ROOT_DIR", tmp_path)

    secure_nodes = tmp_path / "Meta" / "secure_nodes.jsonl"
    secure_nodes.parent.mkdir(parents=True)
    secure_nodes.write_text(
        json.dumps({"sender_id": "openclaw_1", "public_key": "secret123"}),
        encoding="utf-8",
    )

    exo = Exocortex()
    response = exo.process_inbound_pulse(
        "openclaw_1", '{"action": "READ"}', "invalid_hash"
    )
    assert "403" in response


def test_exocortex_accepts_valid_signature(tmp_path, monkeypatch):
    """Proves the Exocortex successfully routes verified external commands."""
    monkeypatch.setattr("System.neuroanatomy.cortical.exocortex.ROOT_DIR", tmp_path)

    secure_nodes = tmp_path / "Meta" / "secure_nodes.jsonl"
    secure_nodes.parent.mkdir(parents=True)
    secure_nodes.write_text(
        json.dumps({"sender_id": "hermes_alpha", "public_key": "secret123"}),
        encoding="utf-8",
    )

    exo = Exocortex()
    payload = '{"action": "READ_RESOURCE", "target": "public_note.md"}'
    valid_sig = hashlib.sha256(f"{payload}secret123".encode()).hexdigest()

    response = exo.process_inbound_pulse("hermes_alpha", payload, valid_sig)
    assert "Content of" in response
