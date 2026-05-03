from pathlib import Path

# Define the absolute root of the Brain OS
ROOT_DIR: Path = Path(__file__).parent.parent.resolve()

# The AI can see everything, but can ONLY write to these specific folders
ALLOWED_DIRECTORIES: set[Path] = {
    ROOT_DIR / "Personal",
    ROOT_DIR / "Professional",
    ROOT_DIR / "Studio",
    ROOT_DIR / "Meta",  # <-- Added Meta
}


def is_safe_path(target_path: Path) -> bool:
    """Check if the target path strictly resides within allowed directories."""
    resolved_target = target_path.resolve()
    for allowed_dir in ALLOWED_DIRECTORIES:
        try:
            resolved_target.relative_to(allowed_dir)
            return True
        except ValueError:
            continue
    return False


def write_safe_file(filepath: str, content: str) -> str:
    """
    Tool for the AI to write files safely.
    Intercepts and blocks any attempt to write outside the sandbox.
    """
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()

        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to write at {target_path}. Allowed zones are Personal/, Professional/, and Studio/."

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

        return target_path.read_text(encoding="utf-8")

    except Exception as e:
        return f"ERROR: Failed to read file - {str(e)}"


def list_safe_directory(directory_path: str) -> str:
    """Lists all files and folders inside a safe directory."""
    try:
        target_path: Path = (ROOT_DIR / directory_path).resolve()

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

        if not is_safe_path(old_path) or not is_safe_path(new_path):
            return "SECURITY BLOCK: Access denied. Both source and destination must be in safe zones."

        if not old_path.exists():
            return f"ERROR: File not found at {old_path.relative_to(ROOT_DIR)}"

        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)

        return f"SUCCESS: Renamed to {new_path.relative_to(ROOT_DIR)}"

    except Exception as e:
        return f"ERROR: Failed to rename file - {str(e)}"


def append_safe_file(filepath: str, content: str) -> str:
    """
    Appends content to a file safely.
    If it detects a </working_memory> tag, it smartly injects the content right before it.
    """
    try:
        target_path: Path = (ROOT_DIR / filepath).resolve()

        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to append at {target_path}."

        if not target_path.exists():
            # If the file doesn't exist yet, just write it normally
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content + "\n", encoding="utf-8")
            return f"SUCCESS: File created and appended at {target_path.relative_to(ROOT_DIR)}"

        # The Shift-Left "Smart Inject" Logic
        current_text = target_path.read_text(encoding="utf-8")

        if "</working_memory>" in current_text:
            new_text = current_text.replace(
                "</working_memory>", f"{content}\n</working_memory>"
            )
            target_path.write_text(new_text, encoding="utf-8")
            return f"SUCCESS: Content smartly injected into <working_memory> at {target_path.relative_to(ROOT_DIR)}"
        else:
            # Fallback standard append
            with open(target_path, "a", encoding="utf-8") as f:
                f.write("\n" + content + "\n")
            return f"SUCCESS: Content appended to the end of {target_path.relative_to(ROOT_DIR)}"

    except Exception as e:
        return f"ERROR: Failed to append to file - {str(e)}"
