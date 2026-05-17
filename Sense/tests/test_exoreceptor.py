import pytest
import json
from Sense.receptors.exoreceptor import ExoReceptor


@pytest.mark.asyncio
async def test_exoreceptor_acp(mocker):
    """Proves the receptor handles REST payloads."""
    receptor = ExoReceptor()
    mock_req = mocker.AsyncMock()
    mock_req.remote = "127.0.0.1"
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

    mock_writer = mocker.Mock()
    mock_writer.write = mocker.Mock()
    mock_writer.close = mocker.Mock()
    mock_writer.drain = mocker.AsyncMock()
    mock_writer.wait_closed = mocker.AsyncMock()
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 12345)

    mocker.patch(
        "Sense.receptors.exoreceptor.transmit_public_signal", return_value="200 OK"
    )

    await receptor.handle_mcp_client(mock_reader, mock_writer)
    mock_writer.write.assert_called_with(b"200 OK")


@pytest.mark.asyncio
async def test_exoreceptor_synaptic_fatigue_ddos(mocker):
    """Proves the Biomimetic Rate Limiter blocks rapid DDoS floods."""
    receptor = ExoReceptor()

    # Restrict the capacity to 2 tokens for testing
    receptor.rate_limiter.capacity = 2.0
    receptor.rate_limiter.refill_rate = 0.0  # No refill during test

    mock_req = mocker.AsyncMock()
    mock_req.remote = "192.168.1.99"
    mock_req.json.return_value = {
        "sender_id": "spammer",
        "payload": "{}",
        "signature": "bad",
    }

    mocker.patch(
        "Sense.receptors.exoreceptor.transmit_public_signal", return_value="200 OK"
    )

    # Pulse 1: Allowed
    resp1 = await receptor.handle_acp_pulse(mock_req)
    assert resp1.status == 200

    # Pulse 2: Allowed
    resp2 = await receptor.handle_acp_pulse(mock_req)
    assert resp2.status == 200

    # Pulse 3: Synaptic Fatigue (429 Too Many Requests)
    resp3 = await receptor.handle_acp_pulse(mock_req)
    assert resp3.status == 429
    assert "Synaptic Fatigue" in resp3.text
