from pathlib import Path


def record_audio(filepath: str, duration: int = 5) -> str:
    """The Physical Ear: Captures raw audio from the host's hardware microphone."""
    try:
        import sounddevice as sd
        import soundfile as sf

        fs = 44100
        print(f"👂 Recording for {duration} seconds...")
        myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        sf.write(filepath, myrecording, fs)
        return f"SUCCESS: Audio recorded to {filepath}"
    except ImportError:
        return "<sensory_error>Missing drivers. Run: uv add sounddevice soundfile numpy</sensory_error>"
    except Exception as e:
        return f"<sensory_error>HEARING ERROR: {str(e)}</sensory_error>"


def play_audio(filepath: str) -> str:
    """The Physical Speaker: Plays a raw audio file out loud."""
    try:
        import sounddevice as sd
        import soundfile as sf

        data, fs = sf.read(filepath)
        print(f"🔊 Playing {filepath}...")
        sd.play(data, fs)
        sd.wait()
        return "SUCCESS: Audio playback complete."
    except Exception as e:
        return f"<sensory_error>PLAYBACK ERROR: {str(e)}</sensory_error>"
