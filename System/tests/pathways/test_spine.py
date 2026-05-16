from System.neuroanatomy.pathways.spine import transduce_to_spine


def test_spinal_cord_somatic_reflex(mocker):
    """Proves the spine intercepts 'reflex' stimuli and routes to somatic motor functions."""
    mock_status = mocker.patch(
        "System.cli_somatic.status", create=True, return_value="System Nominal"
    )
    result = transduce_to_spine("monitor", "crash", stimulus_type="reflex")

    assert result == "System Nominal"
    mock_status.assert_called_once()


def test_spinal_cord_visceral_routing(mocker):
    """Proves the spine passes 'visceral' stimuli directly to the enteric gut."""
    mock_gut = mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction",
        return_value=("True", "Valid", "FAST", "STUDIO", {}),
    )
    result = transduce_to_spine("webhook", "data", stimulus_type="visceral")

    assert result[0] == "True"
    mock_gut.assert_called_once_with("data")


def test_spine_ascending_thalamic(mocker):
    """Proves the spine successfully queues 'exteroceptive' stimuli onto a non-blocking background thread."""
    mock_thread = mocker.patch("System.neuroanatomy.pathways.spine.threading.Thread")

    result = transduce_to_spine("web", "html data", stimulus_type="exteroceptive")

    assert result == "Stimulus from web successfully queued for cognitive processing."
    mock_thread.assert_called_once()
