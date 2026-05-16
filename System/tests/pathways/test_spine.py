from System.neuroanatomy.pathways.spine import transduce_to_spine


def test_spine_somatic_reflex_dynamic(mocker):
    """Proves the spine dynamically fires somatic functions based on the payload string."""
    # We patch a generic command like 'flush' to prove dynamic getattr routing works
    mock_flush = mocker.patch(
        "System.cli_somatic.flush", create=True, return_value="Flushed!"
    )
    result = transduce_to_spine("monitor", "flush", stimulus_type="reflex")

    assert result == "Flushed!"
    mock_flush.assert_called_once()


def test_spine_somatic_reflex_missing():
    """Proves the spine safely rejects reflex requests for non-existent motor functions."""
    result = transduce_to_spine("monitor", "hack_mainframe", stimulus_type="reflex")
    assert "does not exist in cli_somatic" in result


def test_spine_visceral_routing(mocker):
    """Proves the spine passes 'visceral' stimuli directly to the enteric gut."""
    mock_gut = mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction",
        return_value="Digested successfully.",
    )
    result = transduce_to_spine("webhook", "payment_data", stimulus_type="visceral")

    assert result == "Digested successfully."
    mock_gut.assert_called_once_with("payment_data")


def test_spine_visceral_error(mocker):
    """Proves the spine safely catches gut digestion exceptions without crashing the listener thread."""
    mock_gut = mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction",
        side_effect=Exception("Database lock"),
    )
    result = transduce_to_spine("webhook", "bad_data", stimulus_type="visceral")

    assert "Gut error: Database lock" in result
    mock_gut.assert_called_once_with("bad_data")


def test_spine_ascending_thalamic_bbb(mocker):
    """Proves exteroceptive stimuli hit the Blood-Brain Barrier and spawn a Thalamic thread."""
    mock_bbb = mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.scrub_payload",
        create=True,
        return_value="[CLEAN]",
    )
    mock_thread = mocker.patch("System.neuroanatomy.pathways.spine.threading.Thread")

    result = transduce_to_spine("web", "dirty_data", stimulus_type="exteroceptive")

    assert "safely scrubbed and queued for cognition" in result
    mock_bbb.assert_called_once_with("dirty_data")
    mock_thread.assert_called_once()
