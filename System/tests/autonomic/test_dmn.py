# --- System/tests/autonomic/test_dmn.py ---
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
    # 🔐 SHIFT-LEFT REPAIR: Target the original source definition path to avoid inline module namespace collisions
    mocker.patch("System.neuroanatomy.cortical.prefrontal.execute_pipeline")

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


def test_trigger_daydreams_with_thalamic_routing(mocker, tmp_path):
    """
    Zero-Debt Test: Proves the Default Mode Network correctly fetches
    mutated model strings and secure keys from the Vault before dreaming.
    """
    from System.neuroanatomy.autonomic.dmn import trigger_daydreams

    mocker.patch(
        "System.neuroanatomy.autonomic.dmn._gather_dream_context", return_value="Memory"
    )

    # Use Pytest's real tmp_path to prevent internal hashlib/path encoding crashes
    mocker.patch("System.neuroanatomy.autonomic.dmn.ROOT_DIR", tmp_path)
    # Ensure DNA config loads deterministically without touching the disk
    mocker.patch("System.neuroanatomy.autonomic.dmn.get_dna_config", return_value={})
    # 🔐 SHIFT-LEFT REPAIR: Target the original source definition path to avoid inline module namespace collisions
    mocker.patch("System.neuroanatomy.cortical.prefrontal.execute_pipeline")

    # Mock the Immune System Vault to simulate dynamic routing
    mock_vault_resolve = mocker.patch(
        "System.neuroanatomy.autonomic.dmn.vault.resolve_routing",
        return_value=("openrouter/gemini/gemini-2.5-flash", "or-daydream-key"),
    )

    # Mock litellm synchronous completion
    mock_completion = mocker.patch("System.neuroanatomy.autonomic.dmn.completion")
    mock_completion.return_value.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(content="Daydream epiphany generated.")
        )
    ]

    result = trigger_daydreams()

    assert "Daydream cycle completed successfully" in result
    mock_vault_resolve.assert_called_once()

    mock_completion.assert_called_once_with(
        model="openrouter/gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": mocker.ANY}],
        temperature=0.8,
        api_key="or-daydream-key",
    )


def test_trigger_daydreams_zero_key_nightmare(mocker):
    """
    Zero-Debt Test: Proves the sleep cycle fails gracefully into a 'Nightmare'
    if no valid keys are discovered by the Thalamus.
    """
    from System.neuroanatomy.autonomic.dmn import trigger_daydreams
    import litellm  # type: ignore

    mocker.patch(
        "System.neuroanatomy.autonomic.dmn._gather_dream_context", return_value="Memory"
    )

    # Vault returns None for the key
    mocker.patch(
        "System.neuroanatomy.autonomic.dmn.vault.resolve_routing",
        return_value=("gemini/gemini-2.5-flash", None),
    )

    # Simulate LiteLLM rejecting the missing credential
    mocker.patch(
        "System.neuroanatomy.autonomic.dmn.completion",
        side_effect=litellm.exceptions.AuthenticationError(
            message="No API Key", llm_provider="gemini", model="gemini"
        ),
    )

    result = trigger_daydreams()

    # The OS must NOT crash. It must return the Nightmare string safely.
    assert "Nightmare:" in result
    assert "No API Key" in result
