from pathlib import Path
from rich.console import Console
import base64
import cv2

console = Console()


def take_screenshot(url: str, output_path: str) -> str:
    """Uses Headless Chromium to take a full-page screenshot of a URL or localhost."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "VISUAL ERROR: Playwright is not installed. Run `uv pip install playwright`."

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        console.print(
            f"[dim cyan]📸 Sense (Vision): Snapping screenshot of {url}...[/dim cyan]"
        )
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # networkidle ensures React/Vue SPAs finish loading before the screenshot
            page.goto(url, wait_until="networkidle", timeout=15000)
            page.screenshot(path=str(output_file), full_page=True)
            browser.close()

        console.print(f"[bold cyan]✅ Screenshot saved to {output_path}[/bold cyan]")
        return f"SUCCESS: Screenshot saved to {output_path}"
    except Exception as e:
        return f"FATAL SENSE ERROR: Failed to take screenshot. {str(e)}"


def extract_video_frames(video_path: str, max_frames: int = 8) -> list[str]:
    """
    RETINA (Video):
    Extracts evenly spaced frames from a video and returns them as Base64 strings.
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("Failed to open video stream.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        return []

    # Calculate step to get exactly max_frames
    step = max(1, total_frames // max_frames)
    frames_b64 = []

    for i in range(max_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
        ret, frame = cap.read()
        if not ret:
            break

        # Compress and encode to JPG to save memory
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        b64_str = base64.b64encode(buffer).decode("utf-8")
        frames_b64.append(f"data:image/jpeg;base64,{b64_str}")

    cap.release()
    return frames_b64


def capture_webcam_frame() -> str:
    """
    RETINA (Live):
    Snaps a single frame from the default webcam and returns it as a Base64 string.
    """
    import cv2
    import base64

    # 0 is usually the default built-in webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise ValueError(
            "Failed to open physical webcam. Is it plugged in and unblocked?"
        )

    # Warm up the camera sensor (auto-exposure/white balance takes a moment to adjust)
    for _ in range(5):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError("Failed to read frame from webcam.")

    # Compress and encode
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    b64_str = base64.b64encode(buffer).decode("utf-8")

    return f"data:image/jpeg;base64,{b64_str}"
