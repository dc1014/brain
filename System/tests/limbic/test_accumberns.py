from System.neuroanatomy.limbic.nucleus_accumbens import (
    process_dopaminergic_reward,
    get_plasticity_rules,
)


def test_nucleus_accumbens_success(tmp_path, monkeypatch):
    """Proves the brain does not alter rules on success."""
    mock_file = tmp_path / "plasticity_weights.json"
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.nucleus_accumbens.PLASTICITY_FILE", mock_file
    )

    process_dopaminergic_reward("Test task", "Success")
    assert not mock_file.exists()


def test_nucleus_accumbens_failure(tmp_path, mocker, monkeypatch):
    """Proves the brain learns from pain and permanently writes a new behavioral rule."""
    mock_file = tmp_path / "plasticity_weights.json"
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.nucleus_accumbens.PLASTICITY_FILE", mock_file
    )

    class MockMessage:
        content = "Never do that again."

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    mocker.patch(
        "System.neuroanatomy.limbic.nucleus_accumbens.completion",
        return_value=MockResponse(),
    )

    process_dopaminergic_reward("Format hard drive", "Failed: Permission Denied")

    assert mock_file.exists()
    rules = get_plasticity_rules()
    assert "Never do that again." in rules
