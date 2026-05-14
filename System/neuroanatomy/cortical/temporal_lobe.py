from rich.console import Console

console = Console()


def comprehend_sound(
    filepath: str,
    prompt: str = "Analyze this audio. Describe the music, instruments, or environmental sounds you hear.",
) -> str:
    """
    Primary Auditory Cortex: Processes non-vocal audio.
    Leverages Gemini 1.5's native multimodal audio capabilities to understand music and noise.
    """
    from litellm import completion  # type: ignore
    import base64

    try:
        console.print(
            "[dim cyan]🎵 Primary Auditory Cortex analyzing frequencies and rhythm...[/dim cyan]"
        )
        with open(filepath, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

        response = completion(
            model="gemini/gemini-1.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:audio/wav;base64,{audio_b64}"},
                        },
                    ],
                }
            ],
        )
        return str(response.choices[0].message.content)
    except Exception as e:
        return f"SOUND COMPREHENSION ERROR: {str(e)}"
