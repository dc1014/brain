from unittest.mock import MagicMock


def test_extract_video_frames_mocked(tmp_path, monkeypatch):
    """Proves the Retina extracts frames without actually triggering OpenCV hardware."""
    from Sense.receptors.vision import extract_video_frames

    # 1. Setup fake video file
    fake_video = tmp_path / "test.mp4"
    fake_video.touch()

    # 2. Aggressively mock OpenCV's VideoCapture so CI/CD doesn't crash
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 24  # Pretend there are 24 total frames
    # Mock cap.read() to return (True, fake_frame_data)
    mock_cap.read.return_value = (True, b"fake_pixel_data")

    # Mock the cv2 module entirely for this test
    mock_cv2 = MagicMock()
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.imencode.return_value = (True, b"fake_jpg_buffer")
    monkeypatch.setattr("Sense.receptors.vision.cv2", mock_cv2)

    # 3. Execute
    frames = extract_video_frames(str(fake_video), max_frames=8)

    # 4. Assert
    assert len(frames) == 8
    assert frames[0].startswith("data:image/jpeg;base64,")
