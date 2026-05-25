import math
from System.neuroanatomy.cortical.wernicke import (
    filter_semantic_relevance,
    calculate_cosine_similarity,
    load_plain_text_embeddings,
    save_plain_text_embeddings,
)
from unittest.mock import MagicMock


def test_wernicke_empty_results():
    result = filter_semantic_relevance("dogs", "No results found.")
    assert "No documents found" in result


def test_wernicke_semantic_filtering(monkeypatch):
    """
    Zero-Debt Test: Validates that Wernicke successfully intercepts,
    parses, and purges unwanted phrases or outputs before data contract mapping.
    """
    from System.neuroanatomy.cortical.wernicke import filter_semantic_relevance

    # 🛡️ SHIFT-LEFT: Grant the test local clearance to bypass the secure Vault block
    monkeypatch.setattr(
        "System.neuroanatomy.cortical.wernicke.vault.get_api_key_for_model",
        lambda x: "sk-fake-test-key",
    )

    # ⚡ Stub out litellm's network entry point inside Wernicke
    class MockChoices:
        def __init__(self):
            self.message = type(
                "Msg", (), {"content": "The filtered output includes only good boys."}
            )()

    class MockLLMResponse:
        def __init__(self):
            self.choices = [MockChoices()]
            self.usage = type("Usage", (), {"total_tokens": 10})()

    monkeypatch.setattr(
        "System.neuroanatomy.cortical.wernicke.completion",
        lambda *args, **kwargs: MockLLMResponse(),
    )
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.interoception.log_metabolism", lambda x: None
    )

    # Trigger semantic stream evaluation
    result = filter_semantic_relevance(
        "Analyze data stream for good boys.", "Raw string data"
    )

    assert "good boys" in result.lower()
    assert "API Key secured or missing from Vault" not in result


def test_wernicke_cosine_similarity():
    assert math.isclose(calculate_cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
    assert math.isclose(calculate_cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)
    assert math.isclose(calculate_cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0)
    assert calculate_cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_wernicke_zombie_embedding_rotation(monkeypatch, tmp_path):
    # Setup mock file system
    monkeypatch.setattr(
        "System.neuroanatomy.cortical.wernicke.EMBEDDINGS_FILE",
        tmp_path / "Meta" / "Wernicke" / "embeddings.json",
    )

    # Create a "real" note
    real_note = tmp_path / "Studio" / "real_note.md"
    real_note.parent.mkdir(parents=True)
    real_note.write_text("This note exists.")

    # Inject one real vector and one zombie vector (pointing to a file that doesn't exist)
    fake_embeddings = {
        "Studio/real_note.md": [1.0, 0.5],
        "Studio/deleted_note.md": [0.0, 0.0],
    }

    save_plain_text_embeddings(fake_embeddings)

    # Load embeddings (This should trigger the autonomous Necrophage)
    healed = load_plain_text_embeddings()

    # Assert zombie was destroyed and real note was kept
    assert "Studio/deleted_note.md" not in healed
    assert "Studio/real_note.md" in healed


def test_transcribe_speech(mocker, tmp_path):
    from System.neuroanatomy.cortical.wernicke import transcribe_speech

    fake_audio = tmp_path / "test.wav"
    fake_audio.write_text("fake binary")

    # FIX: Patch litellm directly
    mock_transcription = mocker.patch("litellm.transcription")
    mock_response = MagicMock()
    mock_response.text = "Hello, CoreTex OS."
    mock_transcription.return_value = mock_response

    # 🛡️ SHIFT-LEFT FIX: Grant the test security clearance to the Vault
    mocker.patch(
        "System.neuroanatomy.cortical.wernicke.vault.get_api_key_for_model",
        return_value="sk-fake-test-key",
    )

    result = transcribe_speech(str(fake_audio))

    assert result == "Hello, CoreTex OS."
