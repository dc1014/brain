# --- System/tests/limbic/test_hippocampus.py ---
import asyncio
from unittest.mock import patch, MagicMock
from System.neuroanatomy.limbic.hippocampus import (
    _get_conn,
    encode_memory,
    recall_memory,
    rebuild_index,
    _encode_short_term_memory,
)


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
    monkeypatch.setattr("System.neuroanatomy.limbic.hippocampus.ROOT_DIR", tmp_path)
    log_file = tmp_path / "agent_interactions.jsonl"
    lines = [
        '{"domain": "STUDIO", "agent": "Test", "user_prompt": "Build app", "response": "Done"}\n',
        '{"domain": "PERSONAL", "agent": "Test", "user_prompt": "My diary", "response": "Done"}\n',
        '{"domain": "NONE", "agent": "Test", "user_prompt": "General thought", "response": "Done"}\n',
    ]
    log_file.write_text("".join(lines), encoding="utf-8")

    mock_vault.get_api_key_for_model.return_value = "fake_key"
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "- Summary."
    mock_acompletion.return_value = mock_response

    asyncio.run(_encode_short_term_memory())

    assert (tmp_path / "Studio" / "studio-memory.md").exists()
    assert (tmp_path / "Personal" / "personal-memory.md").exists()
    assert (tmp_path / "Meta" / "global-memory.md").exists()


def test_hippocampus_enables_wal_mode_for_concurrency(mocker) -> None:
    mock_connect = mocker.patch(
        "System.neuroanatomy.limbic.hippocampus.sqlite3.connect"
    )
    mock_conn = mock_connect.return_value
    _get_conn()
    mock_conn.execute.assert_any_call("PRAGMA journal_mode=WAL;")
