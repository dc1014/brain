from System.neuroanatomy.pathways.spine import transduce_to_spine


def test_spine_somatic_reflex(mocker):
    """Proves the spine intercepts 'reflex' stimuli and routes to somatic motor functions."""
    mock_status = mocker.patch(
        "System.cli_somatic.status", create=True, return_value="System Nominal"
    )
    result = transduce_to_spine("monitor", "crash", stimulus_type="reflex")

    assert result == "System Nominal"
    mock_status.assert_called_once()


def test_spine_visceral_routing(mocker):
    """Proves the spine passes 'visceral' stimuli directly to the enteric gut."""
    mock_gut = mocker.patch(
        "System.neuroanatomy.systemic.enteric.get_gut_reaction",
        return_value=("True", "Valid", "FAST", "STUDIO", {}),
    )
    result = transduce_to_spine("webhook", "data", stimulus_type="visceral")

    assert result[0] == "True"
    mock_gut.assert_called_once_with("data")


def test_spine_ascending_thalamic(mocker):
    """Proves the spine passes standard 'exteroceptive' stimuli up to the Thalamus."""
    mock_thalamus = mocker.patch(
        "System.neuroanatomy.limbic.thalamus.process_sensory_input",
        create=True,
        return_value="Cognition Triggered",
    )
    result = transduce_to_spine("web", "html data", stimulus_type="exteroceptive")

    assert result == "Cognition Triggered"
    mock_thalamus.assert_called_once_with("web", "html data")


def test_spine_thalamic_fallback():
    """Proves the spine wraps the stimulus safely if the Thalamus module is disconnected."""
    result = transduce_to_spine("audio", "hello world", stimulus_type="exteroceptive")

    assert "<ascending_stimulus source='audio'>" in result
    assert "hello world" in result
