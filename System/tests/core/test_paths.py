import os
import pytest
from System.core.paths import normalize_path, ROOT_DIR


def test_normalize_path_squashes_relative_traversal():
    """Proves the normalizer collapses malicious or messy relative pathing (../)."""
    messy_path = ROOT_DIR / "System" / "tools" / ".." / "config"
    clean_path = normalize_path(messy_path)

    assert ".." not in str(clean_path)
    assert clean_path == (ROOT_DIR / "System" / "config").resolve().absolute()


def test_normalize_path_handles_strings_and_paths():
    """Proves the myelination function is polymorphic and handles both strings and Path objects."""
    str_input = str(ROOT_DIR / "System")
    path_input = ROOT_DIR / "System"

    assert normalize_path(str_input) == normalize_path(path_input)


def test_normalize_path_forces_absolute():
    """Proves the normalizer forces absolute paths to prevent working-directory hijacking."""
    relative_str = "System/config/agents.yaml"
    clean_path = normalize_path(relative_str)

    assert clean_path.is_absolute()


def test_normalize_path_resolves_symlinks(tmp_path):
    """
    ZERO-DEBT: Proves the Symlink Armor (os.path.realpath) strips symbolic links
    and junction points to reveal the true physical path.
    """
    # 1. Create a true physical file
    physical_dir = tmp_path / "physical_safe_zone"
    physical_dir.mkdir()
    target_file = physical_dir / "target.txt"
    target_file.touch()

    # 2. Create a deceptive symlink pointing to the physical file
    symlink_path = tmp_path / "fake_link.txt"

    try:
        os.symlink(target_file, symlink_path)
    except OSError:
        # Windows restricts symlink creation for non-admins without Developer Mode enabled.
        # Skip this specific test gracefully rather than failing the whole suite.
        pytest.skip(
            "Symlink creation requires elevated privileges or Developer Mode on this Windows host."
        )

    # 3. Process the deceptive link through the normalizer
    resolved_path = normalize_path(symlink_path)

    # 4. Strict Validation: The normalizer MUST bypass the link and target the real file
    assert resolved_path == target_file.resolve().absolute()
    assert "fake_link" not in str(resolved_path)
