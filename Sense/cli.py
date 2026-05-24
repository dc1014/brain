import sys
import typer
from rich.console import Console

# Using the flattened import structure
from receptors.web import transduce_web_page
from pathlib import Path

# 🛡️ SHIFT-LEFT: Lock OS process allocation rules before any parallel modules load
from System.core.concurrency import lock_concurrency_defaults

lock_concurrency_defaults()

sys.path.append(str(Path(__file__).parent.parent))

app = typer.Typer(help="Sense: The Sensory Nervous System for Brain OS")
console = Console()

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore


@app.command()
def scrape(
    url: str = typer.Argument(
        ..., help="The URL to transduce into a sensory Action Potential."
    ),
) -> None:
    """
    Fetches external web stimuli, strips noise, and transduces to Markdown.
    Outputs pure XML/Markdown to stdout for UNIX piping.
    Outputs errors to stderr.
    """
    try:
        result = transduce_web_page(url)

        # UNIX PHILOSOPHY: Raw print to stdout.
        print(result)

        if "<sensory_error" in result:
            # ⚡ THE FIX: Use sys.stderr instead of rich console for strict UNIX piping
            import sys

            sys.stderr.write(result + "\n")
            sys.exit(1)

    except Exception as e:
        import sys

        sys.stderr.write(
            f'<sensory_error source="{url}">\n{str(e)}\n</sensory_error>\n'
        )
        sys.exit(1)


@app.command()
def flush() -> None:
    """Lymphatic System: Sweeps metabolic waste (old logs, baks) into compressed tarball archives."""
    from System.neuroanatomy.systemic.lymphatic import flush_waste

    flush_waste()


@app.command()
def purge() -> None:
    """Lymphatic System: Destructively and permanently deletes all tarball archives."""
    from System.neuroanatomy.systemic.lymphatic import purge_waste

    purge_waste()


@app.command()
def sleep() -> None:
    """Pineal Gland: Manually force the OS into a Deep Sleep cycle (Flush + REM)."""
    from System.neuroanatomy.autonomic.pineal import enter_sleep_cycle

    enter_sleep_cycle()


@app.command()
def screenshot(url: str, output: str = "screenshot.png") -> None:
    """Sense: Takes a headless screenshot of a webpage or localhost server."""
    from Sense.receptors.vision import take_screenshot

    result = take_screenshot(url, output)
    console.print(result)


@app.command()
def perceive(
    image_path: str, query: str = "Describe this image in extreme detail."
) -> None:
    """Sense: Uses the Occipital Lobe to read an image file and extract semantic meaning."""
    from System.neuroanatomy.cortical.occipital import perceive_image

    result = perceive_image(image_path, query)
    console.print(result)


@app.command()
def listen(
    duration: int = typer.Option(5, "--duration", "-d", help="Seconds to record"),
    output: str = typer.Option(
        "recording.wav", "--output", "-o", help="Output file path"
    ),
) -> None:
    """The Physical Ear: Activate the microphone to record ambient audio."""
    from Sense.receptors.audio import record_audio
    from pathlib import Path

    target = Path(output)

    # SHIFT-LEFT: Media Quarantine. If no absolute path is given, force it into Media/Recordings
    if target.parent == Path("."):
        out_path = Path(__file__).parent.parent / "Media" / "Recordings" / output
    else:
        out_path = target.resolve()

    out_path.parent.mkdir(parents=True, exist_ok=True)

    console.print(
        f"[bold cyan]🎤 Hardware Mic Active: Recording for {duration} seconds...[/bold cyan]"
    )
    result = record_audio(str(out_path), duration)
    console.print(f"[green]{result}[/green]")


@app.command()
def speak(file: str = typer.Argument(..., help="Path to an audio file to play.")):
    """The Physical Mouth: Plays a raw audio file out loud without cognition."""
    from Sense.receptors.audio import play_audio
    from pathlib import Path

    target = Path(file).resolve()
    if not target.exists():
        console.print(f"[bold red]File not found: {file}[/bold red]")
        return

    console.print(
        f"[bold cyan]🔊 Physical Speaker Active: Playing {file}...[/bold cyan]"
    )
    play_audio(str(target))


@app.command()
def smell(
    directory: str = typer.Argument(
        "Studio", help="The domain to smell for code and semantic rot."
    ),
):
    """The Olfactory Bulb: Runs zero-token static analysis to find dead code and broken links."""
    from System.neuroanatomy.sensory.olfactory import (
        process_scent_profile,
    )  # <--- Ensure this is process_scent_profile, NOT sniff_vault

    console.print(
        f"[bold cyan]👃 Olfactory Bulb smelling '{directory}' for anomalies...[/bold cyan]"
    )
    report = process_scent_profile(
        directory
    )  # <--- Ensure this is process_scent_profile

    if "status='clean'" in report:
        console.print(
            "[bold green]✅ Vault smells clean. No rot detected.[/bold green]"
        )
    else:
        console.print(
            "[bold yellow]⚠️  Anomalies Detected! Scent report written to Meta/Olfactory_Anomalies.md[/bold yellow]"
        )


@app.command()
def taste(
    filepath: str = typer.Argument(
        ..., help="Path to the file to sample (PDF, CSV, LOG)."
    ),
) -> None:
    """The Biological Tongue: Samples massive/dense files into token-safe outputs."""
    import json
    from Sense.receptors.taste import sample_file

    data = sample_file(filepath)
    console.print_json(json.dumps(data))


if __name__ == "__main__":
    app()
