import base64
import time
from pathlib import Path
from rich.console import Console

try:
    import cv2
    import numpy as np

    VISION_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
    VISION_AVAILABLE = False

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
            page.goto(url, wait_until="networkidle", timeout=15000)
            page.screenshot(path=str(output_file), full_page=True)
            browser.close()

        console.print(f"[bold cyan]✅ Screenshot saved to {output_path}[/bold cyan]")
        return f"SUCCESS: Screenshot saved to {output_path}"
    except Exception as e:
        return f"FATAL SENSE ERROR: Failed to take screenshot. {str(e)}"


def extract_video_frames(video_path: str, max_frames: int = 8) -> list[str]:
    """RETINA (Video): Extracts keyframes from a video file as base64 strings."""
    if not cv2:
        return ["ERROR: OpenCV (cv2) is not available in this environment."]

    path = Path(video_path)
    if not path.exists():
        return []

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        return []

    interval = max(1, total_frames // max_frames)
    frames_b64 = []

    for i in range(max_frames):
        frame_id = i * interval
        if frame_id >= total_frames:
            break
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64_str = base64.b64encode(buffer).decode("utf-8")
            frames_b64.append(f"data:image/jpeg;base64,{b64_str}")

    cap.release()
    return frames_b64


def record_webcam_video(save_path: str, duration_seconds: int = 5) -> str:
    """RETINA (Live Temporal): Records video from the physical webcam."""
    if not cv2:
        return "ERROR: OpenCV (cv2) is not available in this environment."

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise ValueError("Failed to open physical webcam for recording.")

    out = None
    try:
        for _ in range(5):
            cap.read()

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 20.0

        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        out = cv2.VideoWriter(save_path, fourcc, fps, (frame_width, frame_height))

        start_time = time.time()

        while int(time.time() - start_time) < duration_seconds:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
            else:
                break

        return f"Webcam video saved to {save_path}"
    finally:
        cap.release()
        if out:
            out.release()


def capture_webcam_frame(save_path: str | None = None) -> str:
    """
    RETINA (Single Frame): Captures a single image from the physical webcam.
    If save_path is provided, saves to disk. Otherwise, returns a base64 string.
    """
    if not cv2:
        return "ERROR: OpenCV (cv2) is not available in this environment."

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "ERROR: Failed to open physical webcam."

    for _ in range(3):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if ret:
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(save_path, frame)
            return f"Webcam frame saved to {save_path}"
        else:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            b64_str = base64.b64encode(buffer).decode("utf-8")
            return f"data:image/jpeg;base64,{b64_str}"

    return "ERROR: Failed to capture webcam frame."
