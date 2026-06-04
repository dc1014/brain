# --- System/core/boot.py ---
import sys
from dotenv import load_dotenv
from System.core.paths import ROOT_DIR


def bootstrap() -> bool:
    """Core initialization hook executed on startup to load configurations and prepare workspace directories."""
    try:
        # Load environment variables using standard ecosystem tools to safely handle quotes and comments
        env_file = ROOT_DIR / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)

        # Initialize parameter state inside the secure memory vault
        from System.neuroanatomy.systemic.immune_system import vault

        vault.secure_environment()

        # ⚡ PHASE 4 FIX: Validate all compiled Markdown agents before boot
        from System.core.dna import get_dna_config
        from rich.console import Console

        console = Console()
        try:
            get_dna_config(force_reload=True)
        except ValueError as e:
            console.print(
                "\n[bold red]🛑 BOOT FAILURE: Agent Configuration Error[/bold red]"
            )
            console.print(f"[red]{e}[/red]\n")
            return False
        except Exception as e:
            console.print(
                "\n[bold red]🛑 BOOT FAILURE: DNA Compiler Crashed[/bold red]"
            )
            console.print(f"[red]{e}[/red]\n")
            return False

        # Batch check structural workspace directories using a primary anchor to reduce filesystem operations
        target_dirs = [
            "Studio",
            "Personal",
            "Professional",
            "Meta",
            "Media",
            "Sense",
            "System/tools/engrams",
            "System/logs",
        ]
        if not (ROOT_DIR / "Meta").exists() or not (ROOT_DIR / "Media").exists():
            for d in target_dirs:
                (ROOT_DIR / d).mkdir(parents=True, exist_ok=True)

        return True
    except Exception as e:
        print(f"Bootstrap failure: {e}", file=sys.stderr)
        return False
