from pathlib import Path
from System.core.paths import ROOT_DIR

# --- SHIFT LEFT SECURITY: OS DIRECTORY BOUNDARIES ---

# The AI can see everything, but can ONLY write to these specific folders
ALLOWED_DIRECTORIES: set[Path] = {
    ROOT_DIR / "Personal",
    ROOT_DIR / "Professional",
    ROOT_DIR / "Studio",
    ROOT_DIR / "Meta",
    ROOT_DIR / "Media",  # The universal binary blob store
}

# The AI can read these directories to understand itself, but CANNOT modify them
READ_ONLY_DIRECTORIES: set[Path] = {
    ROOT_DIR / "System",
}


def is_safe_path(target_path: Path, require_write: bool = False) -> bool:
    """
    SHIFT LEFT: Validates if the target path strictly resides within allowed or read-only directories.
    This must be called BEFORE any file system operation is attempted.
    """
    resolved_target = target_path.resolve()

    # 1. Check Write-Allowed Zones
    for allowed_dir in ALLOWED_DIRECTORIES:
        try:
            resolved_target.relative_to(allowed_dir)
            return True
        except ValueError:
            continue

    # 2. Check Read-Only Zones (if write is not explicitly required)
    if not require_write:
        for ro_dir in READ_ONLY_DIRECTORIES:
            try:
                resolved_target.relative_to(ro_dir)
                return True
            except ValueError:
                continue

    return False
