import base64
import os
import urllib.request
import json
from pathlib import Path
from rich.console import Console
from litellm import completion  # type: ignore

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
    Creates an image from a text prompt (currently via DALL-E 3) and saves it to disk.
    This is the precursor to the 'Spark' external limb.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "VISUAL ERROR: OPENAI_API_KEY is required to generate visual assets."

    output_path = Path("Studio") / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        console.print(
            f"[dim cyan]🎨 Occipital Lobe: Generating visual asset '{output_filename}'...[/dim cyan]"
        )

        # Make direct call to OpenAI Image generation API (Zero-debt, no extra SDKs)
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=json.dumps(
                {"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1024"}
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            image_url = result["data"][0]["url"]

            # Download the resulting image to the filesystem
            urllib.request.urlretrieve(image_url, str(output_path))

        console.print(
            f"[bold cyan]✅ Asset generated and saved to {output_path}[/bold cyan]"
        )
        return f"SUCCESS: Generated visual asset and saved to {output_path}"

    except Exception as e:
        return f"FATAL VISUAL ERROR: Failed to generate asset. {str(e)}"
