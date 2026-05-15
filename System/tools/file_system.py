import json
import shutil
from pathlib import Path
from datetime import datetime
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path, ALLOWED_DIRECTORIES


def write_safe_file(filepath: str, content: str) -> str:
    """Writes files safely, blocking writes outside the sandbox."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path, require_write=True):
            return f"SECURITY BLOCK: Access denied to write at {target_path}."

        # SHIFT-LEFT SAFETY: Block any modification to Architectural Decision Records
        if "adr" in target_path.parts:
            return f"SECURITY BLOCK: Cannot modify ADRs. Human approval required for {filepath}."

        # --- 🦠 IMMUNE SYSTEM REFLEX (Secret Scanning) ---
        from System.neuroanatomy.systemic.immune_system import scan_for_pathogens

        is_clean, immune_reason = scan_for_pathogens(content)
        if not is_clean:
            return immune_reason

        # --- ⚖️ VESTIBULAR REFLEX (Take Snapshot) ---
        from System.neuroanatomy.autonomic.vestibular import create_snapshot

        create_snapshot(filepath)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return f"SUCCESS: File safely written to {target_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to write file - {str(e)}"


def read_safe_file(filepath: str) -> str:
    """Reads the contents of a file within the safe zones."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to read at {target_path}."
        if not target_path.exists():
            return f"ERROR: File not found at {target_path.relative_to(ROOT_DIR)}"
        if not target_path.is_file():
            return "ERROR: Target is not a file."

        # SHIFT-LEFT: XML Framing for Prompt Caching & Attention
        content = target_path.read_text(encoding="utf-8")
        return f'<document path="{filepath}">\n{content}\n</document>'
    except Exception as e:
        return f"ERROR: Failed to read file - {str(e)}"


def list_safe_directory(directory_path: str) -> str:
    """Lists all files and folders inside a safe directory."""
    try:
        target_path: Path = (ROOT_DIR / directory_path).resolve()

        # SHIFT-LEFT: Virtual Root Directory Support (Prevents lethal halts when agents get lost)
        if target_path == ROOT_DIR:
            items = [f"[DIR] {d.name}" for d in ALLOWED_DIRECTORIES if d.exists()]
            return "OS Root. Safe zones available:\n" + "\n".join(items)

        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to list directory at {target_path}."
        if not target_path.exists() or not target_path.is_dir():
            return f"ERROR: Directory not found at {target_path.relative_to(ROOT_DIR)}"

        items = []
        for item in target_path.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{item_type}] {item.name}")
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"ERROR: Failed to list directory - {str(e)}"


def rename_safe_file(old_filepath: str, new_filepath: str) -> str:
    """Renames or moves a file within the safe zones."""
    try:
        old_path: Path = (ROOT_DIR / old_filepath).resolve()
        new_path: Path = (ROOT_DIR / new_filepath).resolve()

        if not is_safe_path(old_path, require_write=True) or not is_safe_path(
            new_path, require_write=True
        ):
            return "SECURITY BLOCK: Access denied. Source and dest must be safe."

        if "adr" in old_path.parts or "adr" in new_path.parts:
            return "SECURITY BLOCK: Cannot modify, move, or create ADRs. Human approval required."

        if not old_path.exists():
            return f"ERROR: File not found at {old_path.relative_to(ROOT_DIR)}"

        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)
        return f"SUCCESS: Renamed to {new_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to rename file - {str(e)}"


def append_safe_file(filepath: str, content: str) -> str:
    """Appends content to a file safely, blocking writes outside the sandbox."""
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()
        if not is_safe_path(target_path, require_write=True):
            return f"SECURITY BLOCK: Access denied to append at {target_path}."

        if "adr" in target_path.parts:
            return f"SECURITY BLOCK: Cannot modify ADRs. Human approval required for {filepath}."

        from System.neuroanatomy.systemic.immune_system import scan_for_pathogens

        is_clean, immune_reason = scan_for_pathogens(content)
        if not is_clean:
            return immune_reason

        from System.neuroanatomy.autonomic.vestibular import create_snapshot

        create_snapshot(filepath)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        prefix = ""
        if target_path.exists():
            with open(target_path, encoding="utf-8") as f:
                current_content = f.read()
                if current_content and not current_content.endswith("\n"):
                    prefix = "\n"

        with open(target_path, "a", encoding="utf-8") as f:
            f.write(prefix + content + "\n")
        return f"SUCCESS: Appended to {target_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to append to file - {str(e)}"


def copy_safe_file(source_filepath: str, dest_filepath: str) -> str:
    """Copies a file from one safe location to another."""
    try:
        source_path: Path = (ROOT_DIR / source_filepath).resolve()
        dest_path: Path = (ROOT_DIR / dest_filepath).resolve()

        if not is_safe_path(source_path) or not is_safe_path(
            dest_path, require_write=True
        ):
            return "SECURITY BLOCK: Access denied. Source and dest must be safe."
        if not source_path.exists():
            return (
                f"ERROR: Source file not found at {source_path.relative_to(ROOT_DIR)}"
            )

        if "adr" in source_path.parts or "adr" in dest_path.parts:
            return "SECURITY BLOCK: Cannot copy ADRs."

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        return f"SUCCESS: Copied to {dest_path.relative_to(ROOT_DIR)}"
    except Exception as e:
        return f"ERROR: Failed to copy file - {str(e)}"


def delete_safe_file(filepath: str) -> str:
    """
    LYSOSOME: Safely removes a file by moving it to a local .trash directory.
    Maintains a manifest for Human-in-the-Loop recovery.
    """
    try:
        target_path = (ROOT_DIR / filepath).resolve()

        if not is_safe_path(target_path, require_write=True):
            return (
                f"SECURITY BLOCK: Cannot delete files outside the sandbox ({filepath})."
            )

        if not target_path.exists():
            return f"ERROR: File {filepath} does not exist."

        if not target_path.is_file():
            return "ERROR: delete_safe_file only works on files, not directories."

        # The Trash Membrane
        trash_dir = ROOT_DIR / ".trash"
        trash_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_trash_name = f"{target_path.stem}_{timestamp}{target_path.suffix}"
        trash_path = trash_dir / safe_trash_name

        # Move the file
        shutil.move(str(target_path), str(trash_path))

        # Log the recovery data
        manifest_path = trash_dir / "manifest.jsonl"
        recovery_data = {
            "deleted_at": timestamp,
            "original_path": str(target_path.relative_to(ROOT_DIR)),
            "trash_path": str(trash_path.relative_to(ROOT_DIR)),
        }
        with open(manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(recovery_data) + "\n")

        return f"SUCCESS: File safely moved to {trash_path.relative_to(ROOT_DIR)}. (Logged in manifest)."

    except Exception as e:
        return f"DELETE ERROR: {str(e)}"
