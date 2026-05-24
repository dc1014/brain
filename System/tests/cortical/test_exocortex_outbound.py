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
async def test_exocortex_outbound_acp(tmp_path, monkeypatch, mocker):
    """Proves ACP (REST) routing functions normally."""
    monkeypatch.setattr("System.neuroanatomy.cortical.exocortex.ROOT_DIR", tmp_path)

    secure_nodes = tmp_path / "Meta" / "secure_nodes.jsonl"
    secure_nodes.parent.mkdir(parents=True)
    secure_nodes.write_text(
        json.dumps({"sender_id": "test_node", "public_key": "123", "acp_port": 8765})
        + "\n",
        encoding="utf-8",
    )

    mock_post_ctx = mocker.AsyncMock()
    mock_post_ctx.__aenter__.return_value.text.return_value = "200 ACP OK"
    mocker.patch("aiohttp.ClientSession.post", return_value=mock_post_ctx)

    exo = Exocortex()
    response = await exo.transmit_outbound_pulse("test_node", "READ", protocol="acp")
    assert "200 ACP OK" in response


@pytest.mark.asyncio
async def test_exocortex_outbound_mcp(tmp_path, monkeypatch, mocker):
    """Proves MCP (TCP) routing was successfully preserved and restored."""
    monkeypatch.setattr("System.neuroanatomy.cortical.exocortex.ROOT_DIR", tmp_path)

    secure_nodes = tmp_path / "Meta" / "secure_nodes.jsonl"
    secure_nodes.parent.mkdir(parents=True)
    secure_nodes.write_text(
        json.dumps({"sender_id": "test_node", "public_key": "123", "mcp_port": 8766})
        + "\n",
        encoding="utf-8",
    )

    # Accurately mock standard asyncio.StreamWriter
    mock_writer = mocker.Mock()
    mock_writer.write = mocker.Mock()  # Sync
    mock_writer.close = mocker.Mock()  # Sync
    mock_writer.drain = mocker.AsyncMock()  # Async
    mock_writer.wait_closed = mocker.AsyncMock()  # Async

    mock_reader = mocker.AsyncMock()
    mock_reader.read.return_value = b"200 MCP OK"

    mocker.patch("asyncio.open_connection", return_value=(mock_reader, mock_writer))

    exo = Exocortex()
    response = await exo.transmit_outbound_pulse("test_node", "READ", protocol="mcp")
    assert "200 MCP OK" in response
