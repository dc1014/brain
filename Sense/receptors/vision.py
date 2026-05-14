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


def capture_webcam_frame(save_path: str | None = None) -> str:
    """
    RETINA (Live):
    Snaps a frame from the webcam. Optionally saves it to disk, then returns Base64.
    """
    import cv2
    import base64

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise ValueError("Failed to open physical webcam.")

    try:
        # Warm up the sensor
        for _ in range(5):
            cap.read()
        ret, frame = cap.read()
    finally:
        # SHIFT-LEFT: Guarantee hardware is released even if the read panics
        cap.release()

    if not ret:
        raise ValueError("Failed to read frame from webcam.")

    # 💾 PHYSICAL MEMORY HOOK: Save to disk if requested
    if save_path:
        from pathlib import Path

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(save_path, frame)

    # Compress and encode
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    b64_str = base64.b64encode(buffer).decode("utf-8")

    return f"data:image/jpeg;base64,{b64_str}"


def record_webcam_video(save_path: str, duration_seconds: int = 5) -> str:
    """
    RETINA (Live Temporal):
    Records a video from the physical webcam for a specified duration and saves it to disk.
    """
    import cv2
    import time
    from pathlib import Path

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise ValueError("Failed to open physical webcam for recording.")

    out = None
    try:
        # Warm up the sensor
        for _ in range(5):
            cap.read()

        # Get camera specifications
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 20.0

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(save_path, fourcc, fps, (frame_width, frame_height))

        start_time = time.time()

        # Strict temporal loop
        while int(time.time() - start_time) < duration_seconds:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
    finally:
        # SHIFT-LEFT: Guarantee hardware and file streams are closed gracefully
        cap.release()
        if out is not None:
            out.release()

    return f"Video successfully recorded to {save_path}"
