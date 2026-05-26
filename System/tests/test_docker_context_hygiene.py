from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_dockerignore_excludes_local_caches_and_virtualenv() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    required_entries = {
        ".git",
        ".venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "*.egg-info",
        "logs",
        ".env",
    }
    assert required_entries.issubset(set(dockerignore))
