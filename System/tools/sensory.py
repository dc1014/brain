import subprocess
from pathlib import Path
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path


def sense_environment(url: str) -> str:
    """Uses the independent Sense organ to fetch and read an external webpage."""
    try:
        # UNIX PHILOSOPHY: Call the external organ via stdout/stderr piping
        result = subprocess.run(
            ["uv", "run", "sense", url], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            return f'<sensory_error source="{url}">\nSense Error: {result.stdout.strip()}\n{result.stderr.strip()}\n</sensory_error>'

        return result.stdout.strip()
    except Exception as e:
        return f'<sensory_error source="{url}">\nFailed to invoke Sense organ: {str(e)}\n</sensory_error>'


def analyze_image(image_path: str, query: str) -> str:
    """Use this to look at and analyze an image file on the disk."""
    from System.neuroanatomy.cortical.occipital import perceive_image

    return perceive_image(image_path, query)


def generate_image(prompt: str, output_filename: str) -> str:
    """Generates a visual asset (PNG/JPG) using an AI image generator."""
    from System.neuroanatomy.cortical.occipital import generate_visual_asset

    return generate_visual_asset(prompt, output_filename)


def capture_screenshot(url: str) -> str:
    """Takes a headless screenshot and explicitly quarantines it in the Meta/Visual_Cortex buffer."""
    from Sense.receptors.vision import take_screenshot

    # Force the screenshot into a quarantined OS buffer
    visual_cortex_dir = ROOT_DIR / "Meta" / "Visual_Cortex"
    visual_cortex_dir.mkdir(parents=True, exist_ok=True)

    output_path = visual_cortex_dir / "latest_screenshot.png"

    take_screenshot(url, str(output_path))
    return f"Screenshot successfully captured and saved to {output_path.as_posix()}"


def speak(text: str) -> str:
    """BROCA + MOUTH: Speaks text out loud to the user."""
    from System.neuroanatomy.cortical.broca import synthesize_speech
    from Sense.receptors.audio import play_audio
    import tempfile

    try:
        out_file = Path(tempfile.gettempdir()) / "brain_tool_speech.mp3"
        synthesize_speech(text, str(out_file))
        play_audio(str(out_file))
        return "SUCCESS: Text spoken out loud to the user."
    except Exception as e:
        return f"SPEECH ERROR: {str(e)}"


def analyze_audio(filepath: str) -> str:
    """TEMPORAL LOBE + WERNICKE: Transcribes speech and analyzes environmental sound."""
    from System.neuroanatomy.cortical.wernicke import transcribe_speech
    from System.neuroanatomy.cortical.temporal_lobe import comprehend_sound

    try:
        target_path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return "SECURITY BLOCK: Cannot access audio files outside the sandbox."

        if not target_path.exists():
            return f"ERROR: File {filepath} does not exist."

        speech = transcribe_speech(str(target_path))
        environment = comprehend_sound(str(target_path))

        return (
            f"<auditory_analysis>\n"
            f"  <speech>\n{speech}\n  </speech>\n"
            f"  <environment>\n{environment}\n  </environment>\n"
            f"</auditory_analysis>"
        )
    except Exception as e:
        return f"AUDIO ANALYSIS ERROR: {str(e)}"


def taste_safe_file(filepath: str) -> str:
    """GUSTATORY: Safely samples large/dense files (PDF, CSV, Logs) to prevent token bloat."""
    from System.neuroanatomy.sensory.gustatory import process_taste_profile

    target_path = (ROOT_DIR / filepath).resolve()
    if not is_safe_path(target_path):
        return f"SECURITY BLOCK: Cannot taste files outside the sandbox ({filepath})."

    return process_taste_profile(filepath)


def analyze_video(video_path: str, query: str) -> str:
    """SENSE (VISION): Analyzes a local video file."""
    from System.neuroanatomy.cortical.occipital import perceive_video

    return perceive_video(video_path, query)


def perceive_webcam(query: str) -> str:
    """SENSE (VISION): Snaps a frame from the physical webcam and analyzes it."""
    from System.neuroanatomy.cortical.occipital import (
        perceive_webcam as _perceive_webcam,
    )

    return _perceive_webcam(query)


def memorize_user_appearance() -> str:
    """SENSE (VISION): Takes a permanent physical snapshot of the user."""
    from System.neuroanatomy.cortical.occipital import memorize_user_appearance as _mem

    return _mem()


def record_user_video(duration_seconds: int = 5) -> str:
    """SENSE (VISION): Records a short physical video of the user via webcam."""
    from System.neuroanatomy.cortical.occipital import record_user_video as _rec

    return _rec(duration_seconds)
