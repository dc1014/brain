from System.neuroanatomy.autonomic.dmn import trigger_daydreams, _gather_dream_context


def test_dmn_gather_context(mocker, tmp_path):
    """Proves the DMN successfully forages files without crashing."""
    mocker.patch("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path)

    # Setup fake memories
    personal_dir = tmp_path / "Personal"
    personal_dir.mkdir()
    (personal_dir / "note.md").write_text("Secret memory.", encoding="utf-8")

    context = _gather_dream_context()
    assert "Secret memory." in context


def test_dmn_trigger_daydreams(mocker, tmp_path):
    """Proves the DMN correctly queries the LLM and writes the Epiphany to disk."""
    mocker.patch("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path)
    mocker.patch(
        "System.neuroanatomy.autonomic.dmn._gather_dream_context",
        return_value="Test context",
    )

    # Mock the LLM Response
    class MockMessage:
        content = "I dreamed of electric sheep."

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    mock_completion = mocker.patch(
        "System.neuroanatomy.autonomic.dmn.completion", return_value=MockResponse()
    )

    result = trigger_daydreams()

    assert result == "Daydream cycle completed successfully."
    mock_completion.assert_called_once()

    # Verify the memory was permanently encoded
    daydream_file = tmp_path / "Meta" / "DMN" / "daydreams.md"
    assert daydream_file.exists()
    assert "electric sheep" in daydream_file.read_text(encoding="utf-8")
