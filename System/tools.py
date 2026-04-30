from pathlib import Path

# Define the absolute root of the Brain OS
ROOT_DIR: Path = Path(__file__).parent.parent.resolve()

# Define explicitly allowed directories (The Sandbox)
ALLOWED_DIRECTORIES: set[Path] = {
    ROOT_DIR / "Personal",
    ROOT_DIR / "Professional",
    ROOT_DIR / "Studio",
}


def is_safe_path(target_path: Path) -> bool:
    """Check if the target path strictly resides within allowed directories."""
    resolved_target = target_path.resolve()
    for allowed_dir in ALLOWED_DIRECTORIES:
        try:
            # If relative_to succeeds, the target is definitively inside the allowed dir
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
        # Combine root and provided path, then resolve to catch '../' attacks
        target_path: Path = (ROOT_DIR / filepath).resolve()

        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to write at {target_path}. Allowed zones are Personal/, Professional/, and Studio/."

        # Ensure the parent directories exist
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        target_path.write_text(content, encoding="utf-8")
        return f"SUCCESS: File safely written to {target_path.relative_to(ROOT_DIR)}"

    except Exception as e:
        return f"ERROR: Failed to write file - {str(e)}"
