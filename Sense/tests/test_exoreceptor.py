from System.neuroanatomy.pathways.spine import transmit_public_signal


def test_spine_bbb_rejection():
    """Proves the Spine drops payloads that are too large to protect the context window."""
    massive_payload = "A" * 9000
    response = transmit_public_signal("openclaw_1", massive_payload, "sig123")
    assert "413 Payload Too Large" in response


def test_spine_to_thalamus_routing(mocker):
    """Proves the signal cleanly traverses the Spine to the Thalamus and strikes the Exocortex."""
    # Mock the final destination to prevent actual file I/O
    mock_exo = mocker.patch(
        "System.neuroanatomy.cortical.exocortex.Exocortex.process_inbound_pulse",
        return_value="200 OK",
    )

    response = transmit_public_signal("hermes_alpha", '{"action": "READ"}', "valid_sig")

    assert response == "200 OK"
    mock_exo.assert_called_once_with("hermes_alpha", '{"action": "READ"}', "valid_sig")
