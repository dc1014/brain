import os
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


def _is_windows_junction(path: Path) -> bool:
    """⚡ KERNEL CHECK: Detects NTFS junction points on Windows."""
    if os.name == "nt" and path.is_dir():
        try:
            import ctypes

            # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return attrs != -1 and bool(attrs & 0x400)
        except Exception:
            pass
    return False


def is_safe_path(target_path: Path | str, require_write: bool = False) -> bool:
    """
    SHIFT LEFT: Validates if the target path strictly resides within allowed or read-only directories.
    This must be called BEFORE any file system operation is attempted.
    """
    # ⚡ ZERO-DEBT: Force all incoming paths through the Myelin Sheath
    resolved_target = normalize_path(target_path)

    # 1. SHIFT-LEFT: Reject symlinks and Windows junctions directly on the target
    if resolved_target.exists():
        if resolved_target.is_symlink() or _is_windows_junction(resolved_target):
            return False

    # 2. SHIFT-LEFT: Reject symlinks and junctions anywhere in the parent chain
    for parent in resolved_target.parents:
        if parent == ROOT_DIR:
            break
        if parent.is_symlink() or _is_windows_junction(parent):
            return False

    # 3. Check Write-Allowed Zones
    for allowed_dir in ALLOWED_DIRECTORIES:
        try:
            resolved_target.relative_to(allowed_dir)
            return True
        except ValueError:
            continue

    # 4. Check Read-Only Zones (if write is not explicitly required)
    if not require_write:
        for ro_dir in READ_ONLY_DIRECTORIES:
            try:
                resolved_target.relative_to(ro_dir)
                return True
            except ValueError:
                continue

    return False
