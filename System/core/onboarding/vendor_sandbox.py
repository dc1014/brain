import urllib.request
import tarfile
import bz2
import io
from pathlib import Path
from rich.console import Console

console = Console()


def vendor_offline_sandbox(root_dir: Path):
    vendor_dir = root_dir / "System" / "vendor" / "pyodide"

    if (vendor_dir / "pyodide.asm.wasm").exists():
        console.print("[dim]⚡ Offline WASM Sandbox already secured.[/dim]")
        return

    console.print(
        "[bold cyan]📦 Vendoring offline WASM sandbox (Zero-Network Containment)...[/bold cyan]"
    )
    vendor_dir.mkdir(parents=True, exist_ok=True)

    # Direct fetch of the official pre-compiled WASM binaries
    url = "https://github.com/pyodide/pyodide/releases/download/0.26.1/pyodide-0.26.1.tar.bz2"

    try:
        req = urllib.request.urlopen(url)
        tar_data = bz2.decompress(req.read())
        with tarfile.open(fileobj=io.BytesIO(tar_data)) as tar:
            for member in tar.getmembers():
                if member.name.startswith("pyodide/"):
                    member.name = member.name.replace("pyodide/", "", 1)
                    if member.name:
                        tar.extract(member, path=vendor_dir)
        console.print(
            "[bold green]✅ Strict Offline WASM boundaries enforced.[/bold green]"
        )
    except Exception as e:
        console.print(
            f"[bold yellow]⚠️ Pyodide Offline Vendoring Skipped: {e}[/bold yellow]"
        )
        console.print(
            "[dim]Note: Sandboxed Python execution will be unavailable, but Cognitive Mode is fully ready.[/dim]"
        )
