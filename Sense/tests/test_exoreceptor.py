import pytest
import json
from Sense.receptors.exoreceptor import ExoReceptor


@pytest.mark.asyncio
async def test_exoreceptor_acp(mocker):
    """Proves the receptor handles REST payloads."""
    receptor = ExoReceptor()
    mock_req = mocker.AsyncMock()
    mock_req.json.return_value = {"sender_id": "x", "payload": "{}", "signature": "y"}

    mocker.patch(
        "Sense.receptors.exoreceptor.transmit_public_signal", return_value="200 OK"
    )
    resp = await receptor.handle_acp_pulse(mock_req)
    assert resp.status == 200


@pytest.mark.asyncio
async def test_exoreceptor_mcp(mocker):
    """Proves the receptor handles raw TCP streams."""
    receptor = ExoReceptor()

    mock_reader = mocker.AsyncMock()
    mock_reader.read.return_value = json.dumps(
        {"sender_id": "x", "payload": "{}", "signature": "y"}
    ).encode()

    # ⚡ ZERO-DEBT: Accurately mock standard asyncio.StreamWriter
    mock_writer = mocker.Mock()
    mock_writer.write = mocker.Mock()  # Sync
    mock_writer.close = mocker.Mock()  # Sync
    mock_writer.drain = mocker.AsyncMock()  # Async
    mock_writer.wait_closed = mocker.AsyncMock()  # Async

    mocker.patch(
        "Sense.receptors.exoreceptor.transmit_public_signal", return_value="200 OK"
    )

    await receptor.handle_mcp_client(mock_reader, mock_writer)

    mock_writer.write.assert_called_once_with(b"200 OK")
