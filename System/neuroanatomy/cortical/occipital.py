import base64
import os
import json
from pathlib import Path
from rich.console import Console
from litellm import completion  # type: ignore
from typing import Any

console = Console()


def _encode_image_to_base64(image_path: str) -> str:
    """Converts a local image file into a base64 string for the Optic Nerve."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def perceive_image(image_path: str, query: str) -> str:
    """
    Occipital Lobe (Perception):
    Takes a local image file, encodes it, and uses a Multimodal LLM to extract meaning.
    """
    path = Path(image_path)
    if not path.exists():
        return (
            f"VISUAL ERROR: Cannot perceive image. File '{image_path}' does not exist."
        )

    # Determine MIME type safely
    ext = path.suffix.lower()
    mime_type = "image/jpeg"
    if ext == ".png":
        mime_type = "image/png"
    elif ext == ".webp":
        mime_type = "image/webp"

    try:
        base64_image = _encode_image_to_base64(str(path))

        console.print(
            f"[dim cyan]👁️ Occipital Lobe: Processing visual data from {path.name}...[/dim cyan]"
        )

        # Use litellm's standard multimodal format
        response = completion(
            model=os.getenv("VISION_MODEL", "gpt-4o-mini"),  # Configurable Baseline
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
        )
        result = str(response.choices[0].message.content)
        return f"Visual Analysis Result:\n{result}"

    except Exception as e:
        return f"FATAL VISUAL ERROR: Failed to process image. {str(e)}"


def generate_visual_asset(prompt: str, output_filename: str) -> str:
    """
    Visual Motor Cortex (Generation):
    Creates an image from a text prompt using OpenAI's modern models.
    """
    from System.neuroanatomy.systemic.immune_system import vault
    from System.core.paths import ROOT_DIR
    import urllib.request
    import urllib.error
    import os
    from rich.console import Console

    console = Console()

    # 1. Fetch API Key securely
    api_key = vault.get_api_key_for_model("openai/gpt-image-1-mini") or os.getenv(
        "OPENAI_API_KEY"
    )
    if not api_key:
        return "SECURITY BLOCK: OPENAI_API_KEY is missing. Cannot generate images."

    # 2. Modern Model Selection (DALL-E is retired)
    model_name = os.getenv("IMAGE_MODEL", "gpt-image-1-mini")

    output_path = (ROOT_DIR / "Studio") / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        console.print(
            f"[dim cyan]🎨 Occipital Lobe: Generating image using {model_name}...[/dim cyan]"
        )

        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=json.dumps(
                {"model": model_name, "prompt": prompt, "n": 1, "size": "1024x1024"}
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            image_data = result["data"][0]

            # 1. Try to extract standard URL (legacy fallback)
            if "url" in image_data:
                urllib.request.urlretrieve(image_data["url"], str(output_path))

            # 2. Try to extract raw Base64 data (Modern GPT-Image behavior)
            elif "b64_json" in image_data:
                import base64

                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(image_data["b64_json"]))

            # 3. Failsafe if OpenAI changed the key name again
            else:
                return f"SECURITY BLOCK: Could not find image data. Available keys: {list(image_data.keys())}"

        console.print(
            f"[bold cyan]✅ Asset generated and saved to {output_path}[/bold cyan]"
        )
        return f"SUCCESS: Generated visual asset and saved to {output_path}"

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        console.print(f"\n[bold red]❌ OPENAI API ERROR: {error_body}[/bold red]")
        return f"SECURITY BLOCK: OpenAI rejected the request. Details: {error_body}"
    except Exception as e:
        return f"SECURITY BLOCK: Unexpected visual error: {str(e)}"


def _validate_video_security(video_path: Path) -> str | None:
    """
    SHIFT-LEFT SECURITY: Validates file size and magic bytes before processing.
    Returns an error string if blocked, or None if safe.
    """
    # 1. File Size Circuit Breaker (50 MB limit)
    max_size = 50 * 1024 * 1024
    if video_path.stat().st_size > max_size:
        return f"SECURITY BLOCK: Video exceeds 50MB limit ({video_path.stat().st_size / 1024 / 1024:.2f}MB)."

    # 2. Magic Bytes Check (MP4 / WebM)
    try:
        with open(video_path, "rb") as f:
            header = f.read(12)

        # MP4 files usually have 'ftyp' starting at byte 4
        is_mp4 = b"ftyp" in header
        # WebM files usually start with 1A 45 DF A3
        is_webm = header.startswith(b"\x1a\x45\xdf\xa3")

        if not (is_mp4 or is_webm):
            return "SECURITY BLOCK: Invalid magic bytes. File does not appear to be a valid MP4 or WebM video."
    except Exception as e:
        return f"SECURITY BLOCK: Could not read file header. {str(e)}"

    return None  # Passed security checks!


def perceive_video(video_path: str, query: str) -> str:
    """
    Occipital Lobe (Temporal Perception):
    Validates video security, extracts frames, and prepares them for LLM analysis.
    """
    path = Path(video_path)
    if not path.exists():
        return (
            f"VISUAL ERROR: Cannot perceive video. File '{video_path}' does not exist."
        )

    # 1. Security Membrane
    security_error = _validate_video_security(path)
    if security_error:
        return security_error

    # 2. Extract Frames via the Retina
    try:
        from Sense.receptors.vision import extract_video_frames

        console.print(
            f"[dim cyan]👁️ Retina: Extracting frames from {path.name}...[/dim cyan]"
        )
        frames = extract_video_frames(str(path), max_frames=8)
    except ImportError:
        return "VISUAL ERROR: OpenCV not installed. Run `uv pip install opencv-python`."
    except Exception as e:
        return f"VISUAL ERROR: Failed to extract frames. {str(e)}"

    # 3. LLM Synthesis (The Visual Cortex)
    try:
        from System.neuroanatomy.systemic.immune_system import vault
        from litellm import completion
        import os

        # Safely extract from the Vault
        api_key = vault.get_api_key_for_model("openai") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "SECURITY BLOCK: OPENAI_API_KEY is missing. Cannot analyze video."

        model_name = os.getenv("VISION_MODEL", "openai/gpt-4o-mini")

        # Build the multimodal payload exactly like a chat completion
        content_array: list[dict[str, Any]] = [{"type": "text", "text": query}]

        # Attach every extracted frame to the vision payload
        for frame_b64 in frames:
            content_array.append({"type": "image_url", "image_url": {"url": frame_b64}})

        messages = [{"role": "user", "content": content_array}]

        console.print(
            f"[dim cyan]🧠 Occipital Lobe: Synthesizing {len(frames)} frames through {model_name}...[/dim cyan]"
        )

        response = completion(model=model_name, messages=messages, api_key=api_key)

        analysis = response.choices[0].message.content
        console.print("[bold cyan]✅ Video Analysis Complete![/bold cyan]")
        return f"VISUAL ANALYSIS: {analysis}"

    except Exception as e:
        return f"SECURITY BLOCK: Failed to synthesize video frames. Details: {str(e)}"
