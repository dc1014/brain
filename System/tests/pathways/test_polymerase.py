import pytest
from pathlib import Path
from System.neuroanatomy.pathways.polymerase import proofread_yaml_dna, PolymeraseError


def test_polymerase_validates_healthy_dna(tmp_path: Path):
    (tmp_path / "models.yaml").write_text("models:\n  m1: 'gpt-4'", encoding="utf-8")
    (tmp_path / "agents.yaml").write_text(
        "agents:\n  a1:\n    name: 'Agent'\n    model: 'm1'\n    system_prompt: 'prompt'",
        encoding="utf-8",
    )
    (tmp_path / "routes.yaml").write_text(
        "routes:\n  FAST:\n    - agent: 'a1'\n      tools: []\n      context: []",
        encoding="utf-8",
    )
    assert proofread_yaml_dna(tmp_path) is True


def test_polymerase_catches_missing_files(tmp_path: Path):
    with pytest.raises(PolymeraseError, match="Missing"):
        proofread_yaml_dna(tmp_path)


def test_polymerase_catches_invalid_model(tmp_path: Path):
    (tmp_path / "models.yaml").write_text("models:\n  m1: 'gpt-4'", encoding="utf-8")
    (tmp_path / "agents.yaml").write_text(
        "agents:\n  a1:\n    name: 'Agent'\n    model: 'unknown'\n    system_prompt: 'prompt'",
        encoding="utf-8",
    )
    (tmp_path / "routes.yaml").write_text(
        "routes:\n  FAST:\n    - agent: 'a1'\n      tools: []\n      context: []",
        encoding="utf-8",
    )
    with pytest.raises(PolymeraseError, match="unknown model"):
        proofread_yaml_dna(tmp_path)
