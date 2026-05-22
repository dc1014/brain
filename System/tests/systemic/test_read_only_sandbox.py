# --- System/tests/systemic/test_read_only_sandbox.py ---
from unittest.mock import patch
from System.tools.sandbox import is_safe_path


def test_read_only_sandbox_directory_traversal(tmp_path):
    """Proves the shift-left directory path checker blocks system traversal leaks."""
    with patch("System.tools.sandbox.ROOT_DIR", tmp_path):
        # 1. Setup simulated paths
        system_dir = tmp_path / "System"
        system_dir.mkdir(parents=True, exist_ok=True)
        studio_dir = tmp_path / "Studio"
        studio_dir.mkdir(parents=True, exist_ok=True)

        # 2. Validation Gates
        assert is_safe_path(studio_dir / "safe_notes.md") is True
        assert (
            is_safe_path(system_dir / "core" / "secrets.yaml", require_write=True)
            is False
        )
