import re
import json
from rich.console import Console
from typing import Any, Union, Type
from pydantic import BaseModel

console = Console()


class AphasiaError(Exception):
    """Raised when the AI fails to articulate a valid data contract."""

    pass


def enforce_data_contract(
    llm_response: str,
    expected_tag: Union[str, Type[BaseModel]],
    expect_json: bool = False,
) -> Any:
    """
    Broca's Area: Validates and auto-heals Hybrid XML/MD/JSON data contracts.
    """
    if not isinstance(expected_tag, str):
        tag_name = expected_tag.__name__
        is_model = True
    else:
        tag_name = expected_tag
        is_model = False

    open_tag = f"<{tag_name}>"
    close_tag = f"</{tag_name}>"

    extracted = ""

    # 1. Primary: Extract via XML tags
    if open_tag in llm_response:
        start_idx = llm_response.find(open_tag) + len(open_tag)
        end_idx = llm_response.find(close_tag)
        if end_idx != -1:
            extracted = llm_response[start_idx:end_idx].strip()
        else:
            extracted = llm_response[start_idx:].strip()
    else:
        extracted = llm_response.strip()

    # 2. Shift-Left Security: Zero-Regex line-array boundary parsing
    # We use chr(96) to generate backticks safely without breaking UI parsers
    fence = chr(96) * 3
    if fence in extracted:
        lines = extracted.splitlines()

        if lines and lines[0].strip().startswith(fence):
            lines.pop(0)

        if lines and lines[-1].strip().startswith(fence):
            lines.pop()

        extracted = "\n".join(lines).strip()

    # 3. Structural Indexing Fallback (If XML tags were missed but JSON is present)
    if (expect_json or is_model) and not (
        extracted.startswith("{") or extracted.startswith("[")
    ):
        start_brace = extracted.find("{")
        start_bracket = extracted.find("[")

        start_idx = -1
        if start_brace != -1 and start_bracket != -1:
            start_idx = min(start_brace, start_bracket)
        elif start_brace != -1:
            start_idx = start_brace
        elif start_bracket != -1:
            start_idx = start_bracket

        if start_idx != -1:
            is_brace = extracted[start_idx] == "{"
            end_token = "}" if is_brace else "]"
            end_idx = extracted.rfind(end_token)

            if end_idx != -1 and end_idx > start_idx:
                extracted = extracted[start_idx : end_idx + 1].strip()

    # 4. JSON & Pydantic Enforcement
    if expect_json or is_model:
        try:
            data = json.loads(extracted)
        except json.JSONDecodeError:
            # Shift-Left: Heal trailing commas
            healed = re.sub(r",\s*([\]}])", r"\1", extracted)
            try:
                data = json.loads(healed)
            except json.JSONDecodeError:
                err_msg = f"BROCA ERROR: Failed to parse JSON. Raw: {extracted}"
                if is_model:
                    raise AphasiaError(err_msg)
                return False, err_msg

        if not isinstance(expected_tag, str):
            try:
                # Upgraded to robust Pydantic v2 validation
                return expected_tag.model_validate(data)
            except Exception as e:
                raise AphasiaError(
                    f"BROCA ERROR: Pydantic Validation Failed - {str(e)}"
                )

        return True, data

    return True, extracted


def synthesize_speech(text: str, output_path: str) -> str:
    """Broca's Motor Area: Converts text into spoken human audio."""
    from litellm import speech  # type: ignore
    from pathlib import Path

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        console.print(
            "[dim yellow]🗣️ Broca's Area articulating text-to-speech...[/dim yellow]"
        )
        response = speech(model="tts-1", voice="alloy", input=text)
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path
    except Exception as e:
        return f"BROCA ERROR: TTS failed - {e}"
