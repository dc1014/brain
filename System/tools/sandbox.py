from pathlib import Path
from System.core.paths import ROOT_DIR, normalize_path

# --- SHIFT LEFT SECURITY: OS DIRECTORY BOUNDARIES ---

# ⚡ ZERO-DEBT: Myelinate the strict OS boundaries at load time
ALLOWED_DIRECTORIES: set[Path] = {
    normalize_path(ROOT_DIR / "Personal"),
    normalize_path(ROOT_DIR / "Professional"),
    normalize_path(ROOT_DIR / "Studio"),
    normalize_path(ROOT_DIR / "Meta"),
    normalize_path(ROOT_DIR / "Media"),  # The universal binary blob store
}

READ_ONLY_DIRECTORIES: set[Path] = {
    normalize_path(ROOT_DIR / "System"),
}


def is_safe_path(target_path: Path | str, require_write: bool = False) -> bool:
    """
    SHIFT LEFT: Validates if the target path strictly resides within allowed or read-only directories.
    This must be called BEFORE any file system operation is attempted.
    """
    # ⚡ ZERO-DEBT: Force all incoming paths through the Myelin Sheath
    resolved_target = normalize_path(target_path)

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
