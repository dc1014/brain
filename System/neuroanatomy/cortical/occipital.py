import base64
import os
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
