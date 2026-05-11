from unittest.mock import MagicMock
from Sense.receptors.audio import record_audio, play_audio


def test_record_audio(mocker, tmp_path):
    mock_sd = MagicMock()
    mock_sf = MagicMock()
    mocker.patch.dict("sys.modules", {"sounddevice": mock_sd, "soundfile": mock_sf})

    filepath = tmp_path / "test.wav"
    result = record_audio(str(filepath), duration=1)

    assert "SUCCESS" in result
    mock_sd.rec.assert_called_once()
    mock_sf.write.assert_called_once()


def test_play_audio(mocker, tmp_path):
    mock_sd = MagicMock()
    mock_sf = MagicMock()
    mock_sf.read.return_value = ("fake_data", 44100)
    mocker.patch.dict("sys.modules", {"sounddevice": mock_sd, "soundfile": mock_sf})

    filepath = tmp_path / "test.wav"
    result = play_audio(str(filepath))

    assert "SUCCESS" in result
    mock_sd.play.assert_called_once()
