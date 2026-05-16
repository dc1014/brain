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

    - If expected_tag is a string: Returns (is_valid, content_string_or_json).
    - If expected_tag is a Pydantic Model: Returns the instantiated model or raises AphasiaError.
    """
    # ⚡ Type Narrowing for Mypy
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
        if end_idx == -1:
            console.print(
                f"[dim yellow]🗣️ Broca's Area Reflex: Auto-healing missing {close_tag} tag.[/dim yellow]"
            )
            extracted = llm_response[start_idx:].strip()
        else:
            extracted = llm_response[start_idx:end_idx].strip()

    # 2. Fallback: Extract from Markdown blocks if XML is missing (for JSON/Models)
    if not extracted and (expect_json or is_model):
        md_match = re.search(r"```json\n(.*?)\n```", llm_response, re.DOTALL)
        if not md_match:
            md_match = re.search(r"```\n(.*?)\n```", llm_response, re.DOTALL)

        if md_match:
            console.print(
                "[dim yellow]🗣️ Broca's Area Reflex: Extracted JSON from Markdown block (No XML tags found).[/dim yellow]"
            )
            extracted = md_match.group(1).strip()

    # 3. Validation
    if not extracted:
        err_msg = f"BROCA ERROR: Missing {open_tag} tag or markdown block."
        if is_model:
            raise AphasiaError(err_msg)
        return False, err_msg

    # 4. Heal "Markdown Bleeding" (hallucinated fences inside XML)
    inner_md_match = re.match(r"^```[a-zA-Z]*\n(.*?)\n```$", extracted, re.DOTALL)
    if inner_md_match:
        extracted = inner_md_match.group(1).strip()

    # 5. Handle JSON Parsing & Pydantic Validation
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
                return expected_tag(**data)
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
        response.stream_to_file(output_path)
        return str(output_path)
    except Exception as e:
        return f"TTS ERROR: {str(e)}"
