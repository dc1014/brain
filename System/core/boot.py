from rich.console import Console
from System.core.paths import ROOT_DIR
from System.neuroanatomy.systemic.immune_system import vault

console = Console()


def _setup_directories():
    """Creates the biological directory structure if it doesn't exist."""
    directories = [
        ROOT_DIR / "Personal",
        ROOT_DIR / "Professional",
        ROOT_DIR / "Studio",
        ROOT_DIR / "Media",
        ROOT_DIR / "System" / "logs",
        ROOT_DIR / "Meta" / "Wernicke",
        ROOT_DIR / "Meta" / "Basal_Ganglia",
        ROOT_DIR / "Meta" / "Visual_Cortex",
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)


def bootstrap() -> bool:
    """
    The Polymerase Boot Sequence.
    Validates the OS environment, secures variables, and hydrates the Vault.
    """
    # 1. Ensure structural integrity
    _setup_directories()

    # 2. SHIFT-LEFT: Secure the environment explicitly during boot, NOT at module import!
    vault.secure_environment()

    # 3. Validate DNA (.env file)
    env_path = ROOT_DIR / ".env"
    env_example_path = ROOT_DIR / ".env.example"

    if not env_path.exists():
        if env_example_path.exists():
            console.print(
                "[yellow]Notice: .env not found. Synthesizing from .env.example...[/yellow]"
            )
            env_path.write_text(env_example_path.read_text(encoding="utf-8"))
        else:
            console.print(
                "[bold red]CRITICAL ERROR: No .env or .env.example file found![/bold red]"
            )
            return False

    return True
