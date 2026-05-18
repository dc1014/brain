from System.neuroanatomy.limbic.hippocampus import (
    encode_memory,
    recall_memory,
    rebuild_index,
    _encode_short_term_memory,
    persist_pipeline_state,
    clear_pipeline_state,
)
from unittest.mock import patch, MagicMock
import asyncio


def test_hippocampus_ephemeral_rebuild(monkeypatch, tmp_path):
    monkeypatch.setattr("System.neuroanatomy.limbic.hippocampus.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.hippocampus.DB_PATH", tmp_path / "hippocampus.db"
    )

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()
    (studio_dir / "app.py").write_text("def secure_auth():\n    return True")

    prof_dir = tmp_path / "Professional"
    prof_dir.mkdir()
    (prof_dir / "notes.md").write_text("The secret project is called Apollo.")

    rebuild_index()

    result_studio = recall_memory("secure_auth")
    assert "app.py" in result_studio
    assert "[MARK] secure_auth [/MARK]" in result_studio

    result_prof = recall_memory("Apollo")
    assert "notes.md" in result_prof
    assert "[MARK] Apollo [/MARK]" in result_prof


def test_hippocampus_injection_safety(monkeypatch, tmp_path):
    monkeypatch.setattr("System.neuroanatomy.limbic.hippocampus.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.hippocampus.DB_PATH", tmp_path / "hippocampus.db"
    )

    encode_memory("test.txt", "Some safe text")
    malicious_query = '""" OR 1=1 --'
    result = recall_memory(malicious_query)

    assert "Hippocampus recall error" not in result


@patch("System.neuroanatomy.limbic.hippocampus.vault")
@patch("System.neuroanatomy.limbic.hippocampus.acompletion")
def test_hippocampus_encodes_memory_all_domains(
    mock_acompletion, mock_vault, tmp_path, monkeypatch
):
    """
    Zero-Debt Test: Ensures the Hippocampus groups logs by multiple domains
    and correctly routes them to their respective domain files.
    """
    monkeypatch.setattr("System.neuroanatomy.limbic.hippocampus.ROOT_DIR", tmp_path)

    # 1. Create fake short-term memory logs mixing domains
    log_file = tmp_path / "agent_interactions.jsonl"
    lines = [
        '{"domain": "STUDIO", "agent": "Test", "user_prompt": "Build app", "response": "Done"}\n',
        '{"domain": "PERSONAL", "agent": "Test", "user_prompt": "My diary", "response": "Done"}\n',
        '{"domain": "NONE", "agent": "Test", "user_prompt": "General thought", "response": "Done"}\n',  # Should map to META
    ]
    log_file.write_text("".join(lines), encoding="utf-8")

    # 2. Mock the LLM Summary Response
    mock_vault.get_api_key_for_model.return_value = "fake_key"
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "- Summary."
    mock_acompletion.return_value = mock_response

    # 3. Trigger Hippocampus
    asyncio.run(_encode_short_term_memory())

    # 4. Strict Validation across ALL domains
    assert (tmp_path / "Studio" / "studio-memory.md").exists()
    assert (tmp_path / "Personal" / "personal-memory.md").exists()
    assert (tmp_path / "Meta" / "global-memory.md").exists()


def test_hippocampus_pipeline_persistence(monkeypatch, tmp_path):
    """Proves the Hippocampus correctly saves and clears pipeline state for crash recovery."""
    import json

    # 1. Isolate the queue file to the test's temp directory
    mock_queue_file = tmp_path / "execution_queue.json"
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.hippocampus.QUEUE_FILE_PATH", mock_queue_file
    )

    # 2. Persist a fake pipeline state
    fake_pipeline = [{"agent": "frontend_engineer"}, {"agent": "qa_auditor"}]
    persist_pipeline_state("Build a button", "FORGE", "STUDIO", fake_pipeline)

    # 3. Assert the file was written with the correct state
    assert mock_queue_file.exists(), "Hippocampus failed to write the state file!"

    with open(mock_queue_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["original_task"] == "Build a button"
    assert data["route_type"] == "FORGE"
    assert len(data["remaining_steps"]) == 2

    # 4. Assert the Lymphatic flush correctly clears the state
    clear_pipeline_state()
    assert not mock_queue_file.exists(), "Hippocampus failed to clear the state file!"
