from pathlib import Path
from rich.console import Console

console = Console()


def take_screenshot(url: str, output_path: str) -> str:
    """Uses Headless Chromium to take a full-page screenshot of a URL or localhost."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "VISUAL ERROR: Playwright is not installed. Run `uv pip install playwright`."

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        console.print(
            f"[dim cyan]📸 Sense (Vision): Snapping screenshot of {url}...[/dim cyan]"
        )
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # networkidle ensures React/Vue SPAs finish loading before the screenshot
            page.goto(url, wait_until="networkidle", timeout=15000)
            page.screenshot(path=str(output_file), full_page=True)
            browser.close()

        console.print(f"[bold cyan]✅ Screenshot saved to {output_path}[/bold cyan]")
        return f"SUCCESS: Screenshot saved to {output_path}"
    except Exception as e:
        return f"FATAL SENSE ERROR: Failed to take screenshot. {str(e)}"
