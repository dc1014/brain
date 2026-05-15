import subprocess
from pathlib import Path
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path
from System.core.schemas import ExecutionResult


def sense_environment(url: str) -> ExecutionResult:
    """Uses the independent Sense organ to fetch and read an external webpage."""
    try:
        result = subprocess.run(
            ["uv", "run", "sense", url], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            reason = f'<sensory_error source="{url}">\nSense Error: {result.stdout.strip()}\n{result.stderr.strip()}\n</sensory_error>'
            return ExecutionResult(
                success=False, output=reason, block_reason="Sense subprocess failed"
            )
        return ExecutionResult(success=True, output=result.stdout.strip())
    except Exception as e:
        reason = f'<sensory_error source="{url}">\nFailed to invoke Sense organ: {str(e)}\n</sensory_error>'
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def analyze_image(image_path: str, query: str) -> ExecutionResult:
    """Use this to look at and analyze an image file on the disk."""
    from System.neuroanatomy.cortical.occipital import perceive_image

    output = perceive_image(image_path, query)
    if "ERROR" in output or "SECURITY BLOCK" in output:
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)


def generate_image(prompt: str, output_filename: str) -> ExecutionResult:
    """Generates a visual asset (PNG/JPG) using an AI image generator."""
    from System.neuroanatomy.cortical.occipital import generate_visual_asset

    output = generate_visual_asset(prompt, output_filename)
    if "ERROR" in output or "SECURITY BLOCK" in output:
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)


def capture_screenshot(url: str) -> ExecutionResult:
    """Takes a headless screenshot and explicitly quarantines it in the Meta/Visual_Cortex buffer."""
    from Sense.receptors.vision import take_screenshot

    visual_cortex_dir = ROOT_DIR / "Meta" / "Visual_Cortex"
    visual_cortex_dir.mkdir(parents=True, exist_ok=True)
    output_path = visual_cortex_dir / "latest_screenshot.png"
    take_screenshot(url, str(output_path))
    return ExecutionResult(
        success=True,
        output=f"Screenshot successfully captured and saved to {output_path.as_posix()}",
    )


def speak(text: str) -> ExecutionResult:
    """BROCA + MOUTH: Speaks text out loud to the user."""
    from System.neuroanatomy.cortical.broca import synthesize_speech
    from Sense.receptors.audio import play_audio
    import tempfile

    try:
        out_file = Path(tempfile.gettempdir()) / "brain_tool_speech.mp3"
        synthesize_speech(text, str(out_file))
        play_audio(str(out_file))
        return ExecutionResult(
            success=True, output="SUCCESS: Text spoken out loud to the user."
        )
    except Exception as e:
        reason = f"SPEECH ERROR: {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def analyze_audio(filepath: str) -> ExecutionResult:
    """TEMPORAL LOBE + WERNICKE: Transcribes speech and analyzes environmental sound."""
    from System.neuroanatomy.cortical.wernicke import transcribe_speech
    from System.neuroanatomy.cortical.temporal_lobe import comprehend_sound

    try:
        target_path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            reason = "SECURITY BLOCK: Cannot access audio files outside the sandbox."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        if not target_path.exists():
            reason = f"ERROR: File {filepath} does not exist."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        speech = transcribe_speech(str(target_path))
        environment = comprehend_sound(str(target_path))

        out_str = (
            f"<auditory_analysis>\n"
            f"  <speech>\n{speech}\n  </speech>\n"
            f"  <environment>\n{environment}\n  </environment>\n"
            f"</auditory_analysis>"
        )
        return ExecutionResult(success=True, output=out_str)
    except Exception as e:
        reason = f"AUDIO ANALYSIS ERROR: {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def taste_safe_file(filepath: str) -> ExecutionResult:
    """GUSTATORY: Safely samples large/dense files (PDF, CSV, Logs) to prevent token bloat."""
    from System.neuroanatomy.sensory.gustatory import process_taste_profile

    target_path = (ROOT_DIR / filepath).resolve()
    if not is_safe_path(target_path):
        reason = f"SECURITY BLOCK: Cannot taste files outside the sandbox ({filepath})."
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    output = process_taste_profile(filepath)
    return ExecutionResult(success=True, output=output)


def analyze_video(video_path: str, query: str) -> ExecutionResult:
    """SENSE (VISION): Analyzes a local video file."""
    from System.neuroanatomy.cortical.occipital import perceive_video

    output = perceive_video(video_path, query)
    if "ERROR" in output or "SECURITY BLOCK" in output:
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)


def perceive_webcam(query: str) -> ExecutionResult:
    """SENSE (VISION): Snaps a frame from the physical webcam and analyzes it."""
    from System.neuroanatomy.cortical.occipital import (
        perceive_webcam as _perceive_webcam,
    )

    output = _perceive_webcam(query)
    if "ERROR" in output or "SECURITY BLOCK" in output:
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)


def memorize_user_appearance() -> ExecutionResult:
    """SENSE (VISION): Takes a permanent physical snapshot of the user."""
    from System.neuroanatomy.cortical.occipital import memorize_user_appearance as _mem

    output = _mem()
    if "ERROR" in output or "SECURITY BLOCK" in output:
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)


def record_user_video(duration_seconds: int = 5) -> ExecutionResult:
    """SENSE (VISION): Records a short physical video of the user via webcam."""
    from System.neuroanatomy.cortical.occipital import record_user_video as _rec

    output = _rec(duration_seconds)
    if "ERROR" in output or "SECURITY BLOCK" in output:
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)
