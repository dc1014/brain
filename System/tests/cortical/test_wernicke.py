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


def test_wernicke_semantic_filtering(mocker):

    class MockResponse:
        class Choice:
            class Message:
                content = "The dog note says they are good boys."

            message = Message()

        choices = [Choice()]
        usage = type("Usage", (), {"total_tokens": 10})()

    mocker.patch(
        "System.neuroanatomy.cortical.wernicke.completion", return_value=MockResponse()
    )
    mocker.patch("System.neuroanatomy.autonomic.interoception.log_metabolism")

    raw_text = "File1: Cats are cool. File2: Dogs are good boys."
    result = filter_semantic_relevance("Tell me about canines", raw_text)

    assert "good boys" in result


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
    mock_response.text = "Hello, Brain OS."
    mock_transcription.return_value = mock_response

    result = transcribe_speech(str(fake_audio))

    assert result == "Hello, Brain OS."
    mock_transcription.assert_called_once()
