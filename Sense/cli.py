import sys
import typer
from rich.console import Console

# Using the flattened import structure
from receptors.web import transduce_web_page

app = typer.Typer(help="Sense: The Sensory Nervous System for Brain OS")
console = Console()

# --- SHIFT-LEFT: CROSS-PLATFORM ENCODING FIX ---
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
# ---------------------------------------------


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
        # Generate the biological Action Potential
        result = transduce_web_page(url)

        # UNIX PHILOSOPHY: Raw print to stdout.
        # Do not use Rich here, or it will inject ANSI color codes into the piped output!
        print(result)

        # If it was an error payload, exit with a non-zero code so downstream pipes know it failed
        if "<sensory_error" in result:
            sys.exit(1)

    except Exception as e:
        # UNIX PHILOSOPHY: Print catastrophic errors to stderr
        console.print(
            f"[bold red]Fatal Sensory Failure:[/bold red] {str(e)}",
            style="red",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    app()
