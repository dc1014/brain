import pytest
import json
from System.neuroanatomy.cortical.exocortex import Exocortex


@pytest.mark.asyncio
async def test_exocortex_outbound_missing_node(tmp_path, monkeypatch):
    """Proves outbound transmission safely aborts if the peer is not in the secure membrane."""
    monkeypatch.setattr("System.neuroanatomy.cortical.exocortex.ROOT_DIR", tmp_path)

    exo = Exocortex()
    response = await exo.transmit_outbound_pulse("ghost_node", "READ_RESOURCE")
    assert "404" in response


@pytest.mark.asyncio
async def test_exocortex_outbound_success(tmp_path, monkeypatch, mocker):
    """Proves the Exocortex correctly hashes and transmits the payload."""
    monkeypatch.setattr("System.neuroanatomy.cortical.exocortex.ROOT_DIR", tmp_path)

    # 1. Setup the secure membrane
    secure_nodes = tmp_path / "Meta" / "secure_nodes.jsonl"
    secure_nodes.parent.mkdir(parents=True)
    node_data = {
        "sender_id": "openclaw_local",
        "public_key": "secret123",
        "host": "127.0.0.1",
        "port": 9999,
    }
    secure_nodes.write_text(json.dumps(node_data) + "\n", encoding="utf-8")

    # 2. Mock the asyncio socket connection
    mock_writer = mocker.AsyncMock()
    mock_reader = mocker.AsyncMock()
    mock_reader.read.return_value = b"200 OK: Execution Started"

    mocker.patch("asyncio.open_connection", return_value=(mock_reader, mock_writer))

    # 3. Fire the pulse
    exo = Exocortex()
    response = await exo.transmit_outbound_pulse(
        "openclaw_local", "EXECUTE_ENGRAM", "deploy_app"
    )

    assert "200 OK" in response
    mock_writer.write.assert_called_once()

    # Extract the payload that was sent and verify the signature logic
    sent_data = json.loads(mock_writer.write.call_args[0][0].decode("utf-8"))
    assert sent_data["sender_id"] == "brain_os_local"
    assert "signature" in sent_data
