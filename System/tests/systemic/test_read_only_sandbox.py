from System.tools import is_safe_path, ROOT_DIR


def test_read_only_sandbox_logic():
    """Mathematically proves that the Blood-Brain Barrier enforces Read-Only zones."""

    # Setup test paths
    system_file = ROOT_DIR / "System" / "runtime.py"
    studio_file = ROOT_DIR / "Studio" / "app.py"
    external_file = ROOT_DIR.parent / "Windows" / "system32.dll"

    # 1. External files should ALWAYS be blocked (Path Traversal Protection)
    assert is_safe_path(external_file) is False
    assert is_safe_path(external_file, require_write=True) is False

    # 2. Allowed directories should allow BOTH read and write
    assert is_safe_path(studio_file) is True
    assert is_safe_path(studio_file, require_write=True) is True

    # 3. Read-Only directories should allow read, but absolutely BLOCK write
    assert is_safe_path(system_file) is True
    assert is_safe_path(system_file, require_write=True) is False
