import re
from rich.console import Console

console = Console()


def enforce_data_contract(llm_response: str, expected_tag: str) -> tuple[bool, str]:
    """
    Broca's Area: Validates and auto-heals Hybrid XML/MD data contracts.
    Returns (is_valid, extracted_content_or_error_msg).
    """
    open_tag = f"<{expected_tag}>"
    close_tag = f"</{expected_tag}>"

    if open_tag not in llm_response:
        return (
            False,
            f"BROCA ERROR: The AI failed to articulate its intent. Missing {open_tag} tag.",
        )

    start_idx = llm_response.find(open_tag) + len(open_tag)
    end_idx = llm_response.find(close_tag)

    if end_idx == -1:
        console.print(
            f"[dim yellow]🗣️ Broca's Area Reflex: Auto-healing missing {close_tag} tag.[/dim yellow]"
        )
        extracted = llm_response[start_idx:].strip()
    else:
        extracted = llm_response[start_idx:end_idx].strip()

    markdown_block_pattern = r"^```[a-zA-Z]*\n(.*?)\n```$"
    match = re.match(markdown_block_pattern, extracted, re.DOTALL)
    if match:
        console.print(
            "[dim yellow]🗣️ Broca's Area Reflex: Stripped hallucinated Markdown block from XML payload.[/dim yellow]"
        )
        extracted = match.group(1).strip()

    if not extracted:
        return False, f"BROCA ERROR: The {open_tag} tag was empty."

    return True, extracted


def synthesize_speech(text: str, output_path: str) -> str:
    """Broca's Motor Area: Converts text into spoken human audio."""
    from litellm import speech  # type: ignore
    from rich.console import Console
    from pathlib import Path

    console = Console()
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        console.print(
            "[dim yellow]🗣️ Broca's Area articulating text-to-speech...[/dim yellow]"
        )
        response = speech(model="tts-1", voice="alloy", input=text)
        response.stream_to_file(output_path)
        return str(output_path)
    except Exception as e:
        return f"TTS ERROR: {str(e)}"
