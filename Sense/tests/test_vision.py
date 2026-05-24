import sys
from pathlib import Path
from unittest.mock import MagicMock

from Sense.receptors.vision import (
    extract_video_frames,
    take_screenshot,
    record_webcam_video,
)


def test_extract_video_frames_mocked(tmp_path, monkeypatch):
    """Proves the Retina extracts frames without actually triggering OpenCV hardware."""
    # 1. Setup fake video file
    fake_video = tmp_path / "test.mp4"
    fake_video.touch()

    # 2. Aggressively mock OpenCV's VideoCapture so CI/CD doesn't crash
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 24  # Pretend there are 24 total frames
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


def test_take_screenshot_success(monkeypatch, tmp_path):
    # 1. Setup a dummy output path
    output_path = tmp_path / "test_screenshot.png"

    # 2. Mock Playwright via sys.modules
    class MockPage:
        def goto(self, url, **kwargs):
            pass

        def screenshot(self, path, **kwargs):
            Path(path).write_text("fake_png_data", encoding="utf-8")

    class MockBrowser:
        def new_page(self):
            return MockPage()

        def close(self):
            pass

    class MockChromium:
        def launch(self, **kwargs):
            return MockBrowser()

    class MockPlaywright:
        @property
        def chromium(self):
            return MockChromium()

    class MockSyncPlaywright:
        def __enter__(self):
            return MockPlaywright()

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    # Create a fake module to inject into sys.modules
    class FakePlaywrightModule:
        sync_playwright = MockSyncPlaywright

    monkeypatch.setitem(sys.modules, "playwright.sync_api", FakePlaywrightModule())

    # 3. Execute
    result = take_screenshot("http://localhost:3000", str(output_path))

    # 4. Assert
    assert "SUCCESS" in result
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "fake_png_data"


def test_take_screenshot_handles_playwright_missing(monkeypatch):
    # Simulate Playwright not being installed by injecting None into sys.modules
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)

    result = take_screenshot("http://localhost:3000", "dummy.png")
    assert "VISUAL ERROR" in result
    assert "Playwright is not installed" in result


def test_record_webcam_video_mocked(tmp_path, mocker):
    """Fully mocks OpenCV to simulate a successful read/write hardware loop."""
    mock_cv2 = mocker.patch("Sense.receptors.vision.cv2")

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    # Safe mock read function prevents StopIteration
    call_count = [0]

    def safe_mock_read(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] <= 6:
            return (True, "mock_frame")
        return (False, None)

    mock_cap.read.side_effect = safe_mock_read
    mock_cv2.VideoCapture.return_value = mock_cap

    mock_writer = MagicMock()
    mock_cv2.VideoWriter.return_value = mock_writer

    output_path = str(tmp_path / "test_out.mp4")

    # Execute
    result = record_webcam_video(output_path)

    # Assertions
    assert mock_writer.write.called
    # ⚡ THE LINTER FIX: Removed redundant str() call since result is already a string
    assert "test_out.mp4" in result
