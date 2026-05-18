import sys
from pathlib import Path
from Sense.receptors.vision import take_screenshot


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
