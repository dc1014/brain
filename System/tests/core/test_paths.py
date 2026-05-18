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
