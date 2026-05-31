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


def test_hippocampus_goal_state_machine_sync(tmp_path, mocker):
    """Proves the Python Linter auto-tags new goals and checks off completed ones deterministically."""
    from System.neuroanatomy.limbic.hippocampus import _lint_and_sync_goals
    import json

    mocker.patch("System.neuroanatomy.limbic.hippocampus.ROOT_DIR", tmp_path)
    meta_dir = tmp_path / "Meta"
    meta_dir.mkdir(parents=True)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)

    goals_file = meta_dir / "Goals.md"
    log_file = logs_dir / "agent_interactions.jsonl"

    # 1. Simulate user manually typing goals (one tagged, one completely untagged)
    initial_goals = (
        "# 🎯 Master Goals\n"
        "## Goal: Test the OS\n"
        "- [ ] Write unit tests #goal/ab12\n"
        "- [ ] Write documentation\n"  # Missing tag!
    )
    goals_file.write_text(initial_goals, encoding="utf-8")

    # 2. Simulate the Orchestrator successfully completing #goal/ab12
    dummy_log = {
        "timestamp": "2026-05-31 12:00:00",
        "agent": "coder",
        "response": "Tests written successfully.",
        "goal_thread": "#goal/ab12",
    }
    log_file.write_text(json.dumps(dummy_log) + "\n", encoding="utf-8")

    # 3. Run the zero-token sweep
    _lint_and_sync_goals()

    # 4. Assertions
    new_goals = goals_file.read_text(encoding="utf-8")

    # Assert it checked off the completed one
    assert "- [x] Write unit tests #goal/ab12" in new_goals

    # Assert it auto-generated a tag for the untagged one
    assert "- [ ] Write documentation #goal/" in new_goals
    assert (
        "- [ ] Write documentation\n" not in new_goals
    )  # Ensure the untagged version is gone
