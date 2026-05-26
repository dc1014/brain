import os
import platform
from pathlib import Path
from System.core.paths import ROOT_DIR
from System.core.onboarding.security import _atomic_write_text


def bind_global_alias() -> bool:
    """
    Safely injects a global 'ctx' alias/function into the user's shell profile
    so they can access the OS from anywhere on their machine without breaking CWD.
    """
    os_name = platform.system()
    home = Path.home()
    abs_root = Path(ROOT_DIR).resolve()

    if os_name == "Windows":
        # OneDrive silently relocates user Documents folders on modern Windows environments
        documents_paths = [home / "Documents", home / "OneDrive" / "Documents"]

        profiles = []
        for doc_base in documents_paths:
            # Interrogate profiles for both classic Windows PowerShell (v5.1) and modern PowerShell Core (v7+)
            profiles.append(
                doc_base / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
            )
            profiles.append(
                doc_base / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
            )

        # Directly route to the localized virtual environment interpreter to avoid global path state issues
        target_engine = abs_root / ".venv" / "Scripts" / "python.exe"
        alias_cmd = f"\nfunction ctx {{ & '{target_engine}' -m System.cli $args }}\n"

        success = False
        for profile_path in profiles:
            try:
                profile_path.parent.mkdir(parents=True, exist_ok=True)
                existing_content = ""
                if profile_path.exists():
                    existing_content = profile_path.read_text(encoding="utf-8")
                    if (
                        f"'{target_engine}'" in existing_content
                        or "function ctx" in existing_content
                    ):
                        success = True
                        continue

                new_content = existing_content + alias_cmd
                _atomic_write_text(profile_path, new_content)
                success = True
            except Exception:
                continue
        return success

    else:
        # Mac/Linux (zsh is default on Mac, bash on Linux)
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            profile_path = home / ".zshrc"
        else:
            profile_path = home / ".bashrc"

        target_engine = abs_root / ".venv" / "bin" / "python"

        # Absolute execution bypasses the need to change directories.
        # This keeps the user in their active directory ($PWD), allowing local context processing to work.
        alias_cmd = f"\nalias ctx=\"'{target_engine}' -m System.cli\"\n"

        try:
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            existing_content = ""
            if profile_path.exists():
                existing_content = profile_path.read_text(encoding="utf-8")
                if (
                    f"'{target_engine}'" in existing_content
                    or "alias ctx=" in existing_content
                ):
                    return True

            new_content = existing_content + alias_cmd
            _atomic_write_text(profile_path, new_content)
            return True
        except Exception:
            return False
