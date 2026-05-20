import pytest
import json
from pathlib import Path
from System.tools.ingestion import KnowledgeIngestor


@pytest.fixture
def temp_workspace(tmp_path):
    """Generates a sandboxed workspace layout imitating Brain OS path bounds."""
    root = tmp_path / "brain"
    root.mkdir()
    (root / "System" / "logs").mkdir(parents=True, exist_ok=True)
    return root


def test_should_ignore_rules(temp_workspace, monkeypatch):
    monkeypatch.setattr("System.core.paths.ROOT_DIR", temp_workspace)
    ingestor = KnowledgeIngestor("Personal", ["test"])

    assert ingestor.should_ignore(Path("src/.git/config")) is True
    assert ingestor.should_ignore(Path("src/node_modules/package/index.js")) is True
    assert ingestor.should_ignore(Path("src/components/Button.tsx")) is False


def test_format_handles_nested_backticks(temp_workspace, monkeypatch):
    monkeypatch.setattr("System.core.paths.ROOT_DIR", temp_workspace)
    ingestor = KnowledgeIngestor("Personal", ["dev"])

    file_path = Path("test_code.md")
    origin = Path(".")
    complex_content = "This is a block:\n```python\nprint('hello')\n```\nEnd of block."

    result = ingestor.format_to_hybrid_contract(file_path, origin, complex_content)

    # Outer block fence dynamically grows to four backticks to escape nested three-backtick fences
    assert "````md" in result  # ✅ Matches the .md extension of file_path
    assert "````" in result
    assert '<ingested_source path="test_code.md">' in result


def test_successful_file_ingestion(temp_workspace, monkeypatch):
    monkeypatch.setattr("System.core.paths.ROOT_DIR", temp_workspace)

    source_dir = temp_workspace / "external_source"
    source_dir.mkdir()
    sample_file = source_dir / "readme.txt"
    sample_file.write_text("Authoritative knowledge content stream.", encoding="utf-8")

    ingestor = KnowledgeIngestor("Personal", ["seeded"])
    notes, byte_count = ingestor.ingest(sample_file)

    assert notes == 1
    assert byte_count > 0

    dest_note = temp_workspace / "Personal" / "Ingested_readme.txt.md"
    assert dest_note.exists()
    assert "#seeded" in dest_note.read_text(encoding="utf-8")

    log_jsonl = temp_workspace / "System" / "logs" / "agent_interactions.jsonl"
    assert log_jsonl.exists()

    with open(log_jsonl, "r", encoding="utf-8") as f:
        log_data = json.loads(f.readline())
        assert log_data["event"] == "knowledge_absorption"
        assert log_data["file"] == "readme.txt"


def test_skips_empty_and_binary_payloads(temp_workspace, monkeypatch):
    monkeypatch.setattr("System.core.paths.ROOT_DIR", temp_workspace)
    ingestor = KnowledgeIngestor("Personal", [])

    binary_file = temp_workspace / "image.png"
    binary_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    empty_file = temp_workspace / "void.txt"
    empty_file.write_text("   \n   ", encoding="utf-8")

    notes_bin, _ = ingestor.ingest(binary_file)
    notes_emp, _ = ingestor.ingest(empty_file)

    assert notes_bin == 0
    assert notes_emp == 0
