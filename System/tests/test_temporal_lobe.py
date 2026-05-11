from unittest.mock import MagicMock
from System.organs.temporal_lobe import comprehend_sound


def test_comprehend_sound(mocker, tmp_path):
    fake_audio = tmp_path / "test.wav"
    fake_audio.write_text("fake binary")

    # FIX: Patch litellm directly
    mock_completion = mocker.patch("litellm.completion")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="I hear a piano."))]
    mock_completion.return_value = mock_response

    result = comprehend_sound(str(fake_audio))

    assert "piano" in result
    mock_completion.assert_called_once()
