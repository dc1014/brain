# --- System/core/onboarding/path_binding.py ---
import os
import platform
from pathlib import Path
from System.core.paths import ROOT_DIR
from System.core.onboarding.security import _atomic_write_text


def bind_global_alias() -> bool:
    """
    Safely injects a global 'brain' alias into the user's shell profile
    so they can access the OS from anywhere on their machine.
    """
    os_name = platform.system()
    home = Path.home()

    # Define the absolute command to trigger the Brain CLI
    abs_root = str(ROOT_DIR.resolve())

    if os_name == "Windows":
        # PowerShell Profile
        profile_path = (
            home
            / "Documents"
            / "WindowsPowerShell"
            / "Microsoft.PowerShell_profile.ps1"
        )
        alias_cmd = f"\nfunction brain {{ Set-Location '{abs_root}'; uv run python -m System.cli $args }}\n"
    else:
        # Mac/Linux (zsh is default on Mac, bash on Linux)
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            profile_path = home / ".zshrc"
        else:
            profile_path = home / ".bashrc"

        alias_cmd = (
            f"\nalias brain=\"cd '{abs_root}' && uv run python -m System.cli\"\n"
        )

    # Ensure the parent directory exists (especially for Windows)
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if we already injected it to maintain Zero Debt
    existing_content = ""
    if profile_path.exists():
        existing_content = profile_path.read_text(encoding="utf-8")
        if "alias brain=" in existing_content or "function brain" in existing_content:
            return True  # Already installed

    # Shift-Left: Append safely
    try:
        new_content = existing_content + alias_cmd
        _atomic_write_text(profile_path, new_content)
        return True
    except Exception:
        return False
