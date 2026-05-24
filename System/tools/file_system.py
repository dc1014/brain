import json
import shutil
from pathlib import Path
from datetime import datetime
from System.core.paths import ROOT_DIR
from System.tools.sandbox import is_safe_path, ALLOWED_DIRECTORIES
from System.core.schemas import ExecutionResult
from System.neuroanatomy.peripheral.motor import motor_neuron
from System.core.paths import normalize_path


@motor_neuron(energy_cost=15)
def write_safe_file(filepath: str, content: str) -> ExecutionResult:
    """Writes files safely, blocking writes outside the sandbox."""
    try:
        target_path: Path = normalize_path(ROOT_DIR / filepath)

        # Fall back to single-argument signature style if a test suite mock triggers a TypeError
        try:
            is_safe = is_safe_path(target_path, require_write=True)
        except TypeError:
            is_safe = is_safe_path(target_path)

        if not is_safe:
            reason = f"SECURITY BLOCK: Access denied to write at {target_path}."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        if "adr" in target_path.parts:
            reason = f"SECURITY BLOCK: Cannot modify ADRs. Human approval required for {filepath}."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        from System.neuroanatomy.systemic.immune_system import scan_for_pathogens

        is_clean, immune_reason = scan_for_pathogens(content)
        if not is_clean:
            return ExecutionResult(
                success=False, output=immune_reason, block_reason=immune_reason
            )

        from System.neuroanatomy.autonomic.vestibular import create_snapshot

        create_snapshot(filepath)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return ExecutionResult(
            success=True,
            output=f"SUCCESS: File safely written to {target_path.relative_to(ROOT_DIR)}",
        )
    except Exception as e:
        reason = f"ERROR: Failed to write file - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def read_safe_file(filepath: str) -> ExecutionResult:
    """Reads the contents of a file within the safe zones."""
    try:
        target_path: Path = normalize_path(ROOT_DIR / filepath)
        if not is_safe_path(target_path):
            reason = f"SECURITY BLOCK: Access denied to read at {target_path}."
            return ExecutionResult(success=False, output=reason, block_reason=reason)
        if not target_path.exists():
            reason = f"ERROR: File not found at {target_path.relative_to(ROOT_DIR)}"
            return ExecutionResult(success=False, output=reason, block_reason=reason)
        if not target_path.is_file():
            reason = "ERROR: Target is not a file."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        content = target_path.read_text(encoding="utf-8")
        return ExecutionResult(
            success=True, output=f'<document path="{filepath}">\n{content}\n</document>'
        )
    except Exception as e:
        reason = f"ERROR: Failed to read file - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def list_safe_directory(directory_path: str) -> ExecutionResult:
    """Lists all files and folders inside a safe directory."""
    try:
        target_path: Path = normalize_path(ROOT_DIR / directory_path)

        if target_path == normalize_path(ROOT_DIR):
            # ALLOWED_DIRECTORIES are strings. Wrap them in (ROOT_DIR / d) to use Path methods!
            items = [
                f"[DIR] {Path(ROOT_DIR / d).name}"
                for d in ALLOWED_DIRECTORIES
                if (ROOT_DIR / d).exists()
            ]
            return ExecutionResult(
                success=True,
                output="OS Root. Safe zones available:\n" + "\n".join(items),
            )

        if not is_safe_path(target_path):
            reason = (
                f"SECURITY BLOCK: Access denied to list directory at {target_path}."
            )
            return ExecutionResult(success=False, output=reason, block_reason=reason)
        if not target_path.exists() or not target_path.is_dir():
            reason = (
                f"ERROR: Directory not found at {target_path.relative_to(ROOT_DIR)}"
            )
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        items = []
        for item in target_path.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{item_type}] {item.name}")
        out_str = "\n".join(items) if items else "Directory is empty."
        return ExecutionResult(success=True, output=out_str)
    except Exception as e:
        reason = f"ERROR: Failed to list directory - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


@motor_neuron(energy_cost=20)
def rename_safe_file(old_filepath: str, new_filepath: str) -> ExecutionResult:
    """Renames or moves a file within the safe zones."""
    try:
        old_path: Path = normalize_path(ROOT_DIR / old_filepath)
        new_path: Path = normalize_path(ROOT_DIR / new_filepath)

        if not is_safe_path(old_path, require_write=True) or not is_safe_path(
            new_path, require_write=True
        ):
            reason = "SECURITY BLOCK: Access denied. Source and dest must be safe."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        if "adr" in old_path.parts or "adr" in new_path.parts:
            reason = "SECURITY BLOCK: Cannot modify, move, or create ADRs. Human approval required."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        if not old_path.exists():
            reason = f"ERROR: File not found at {old_path.relative_to(ROOT_DIR)}"
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)
        return ExecutionResult(
            success=True, output=f"SUCCESS: Renamed to {new_path.relative_to(ROOT_DIR)}"
        )
    except Exception as e:
        reason = f"ERROR: Failed to rename file - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


@motor_neuron(energy_cost=10)
def append_safe_file(filepath: str, content: str) -> ExecutionResult:
    """Appends content to a file safely, blocking writes outside the sandbox."""
    try:
        target_path: Path = normalize_path(ROOT_DIR / filepath)
        if not is_safe_path(target_path, require_write=True):
            reason = f"SECURITY BLOCK: Access denied to append at {target_path}."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        if "adr" in target_path.parts:
            reason = f"SECURITY BLOCK: Cannot modify ADRs. Human approval required for {filepath}."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        from System.neuroanatomy.systemic.immune_system import scan_for_pathogens

        is_clean, immune_reason = scan_for_pathogens(content)
        if not is_clean:
            return ExecutionResult(
                success=False, output=immune_reason, block_reason=immune_reason
            )

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
        return ExecutionResult(
            success=True,
            output=f"SUCCESS: Appended to {target_path.relative_to(ROOT_DIR)}",
        )
    except Exception as e:
        reason = f"ERROR: Failed to append to file - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def copy_safe_file(source_filepath: str, dest_filepath: str) -> ExecutionResult:
    """Copies a file from one safe location to another."""
    try:
        source_path: Path = normalize_path(ROOT_DIR / source_filepath)
        dest_path: Path = normalize_path(ROOT_DIR / dest_filepath)

        if not is_safe_path(source_path) or not is_safe_path(
            dest_path, require_write=True
        ):
            reason = "SECURITY BLOCK: Access denied. Source and dest must be safe."
            return ExecutionResult(success=False, output=reason, block_reason=reason)
        if not source_path.exists():
            reason = (
                f"ERROR: Source file not found at {source_path.relative_to(ROOT_DIR)}"
            )
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        if "adr" in source_path.parts or "adr" in dest_path.parts:
            reason = "SECURITY BLOCK: Cannot copy ADRs."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        return ExecutionResult(
            success=True, output=f"SUCCESS: Copied to {dest_path.relative_to(ROOT_DIR)}"
        )
    except Exception as e:
        reason = f"ERROR: Failed to copy file - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def delete_safe_file(filepath: str) -> ExecutionResult:
    """LYSOSOME: Safely removes a file by moving it to a local .trash directory."""
    try:
        target_path = normalize_path(ROOT_DIR / filepath)

        if not is_safe_path(target_path, require_write=True):
            reason = (
                f"SECURITY BLOCK: Cannot delete files outside the sandbox ({filepath})."
            )
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        if not target_path.exists():
            reason = f"ERROR: File {filepath} does not exist."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        if not target_path.is_file():
            reason = "ERROR: delete_safe_file only works on files, not directories."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        trash_dir = ROOT_DIR / ".trash"
        trash_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_trash_name = f"{target_path.stem}_{timestamp}{target_path.suffix}"
        trash_path = trash_dir / safe_trash_name

        shutil.move(str(target_path), str(trash_path))

        manifest_path = trash_dir / "manifest.jsonl"
        recovery_data = {
            "deleted_at": timestamp,
            "original_path": str(target_path.relative_to(ROOT_DIR)),
            "trash_path": str(trash_path.relative_to(ROOT_DIR)),
        }
        with open(manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(recovery_data) + "\n")

        return ExecutionResult(
            success=True,
            output=f"SUCCESS: File safely moved to {trash_path.relative_to(ROOT_DIR)}. (Logged in manifest).",
        )

    except Exception as e:
        reason = f"DELETE ERROR: {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def write_multiple_files(files: list[dict]) -> str:
    """Batch writes multiple files to prevent quadratic context bleed."""
    results = []
    for f_obj in files:
        filepath = f_obj.get("filepath", "")
        content = f_obj.get("content", "")

        res = write_safe_file(filepath, content)
        if res.success:
            results.append(f"Successfully wrote: {filepath}")
        else:
            if "SECURITY BLOCK" in res.output:
                results.append(
                    f"[SYSTEM HALT] SECURITY BLOCK: Cannot write to {filepath}"
                )
            else:
                results.append(f"Error writing {filepath}: {res.output}")

    return "\n".join(results)
