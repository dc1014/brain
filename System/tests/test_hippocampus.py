from System.organs.hippocampus import encode_memory, recall_memory, rebuild_index


def test_hippocampus_ephemeral_rebuild(monkeypatch, tmp_path):
    monkeypatch.setattr("System.organs.hippocampus.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "System.organs.hippocampus.DB_PATH", tmp_path / "hippocampus.db"
    )

    # 1. Create Flat File reality in multiple domains
    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()
    (studio_dir / "app.py").write_text("def secure_auth():\n    return True")

    prof_dir = tmp_path / "Professional"
    prof_dir.mkdir()
    (prof_dir / "notes.md").write_text("The secret project is called Apollo.")

    # 2. Rebuild the index from flat files
    rebuild_index()

    # 3. Recall should work across domains
    result_studio = recall_memory("secure_auth")
    assert "app.py" in result_studio
    assert "[MARK] secure_auth [/MARK]" in result_studio

    result_prof = recall_memory("Apollo")
    assert "notes.md" in result_prof
    assert "[MARK] Apollo [/MARK]" in result_prof


def test_hippocampus_injection_safety(monkeypatch, tmp_path):
    monkeypatch.setattr("System.organs.hippocampus.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "System.organs.hippocampus.DB_PATH", tmp_path / "hippocampus.db"
    )

    encode_memory("test.txt", "Some safe text")
    malicious_query = '""" OR 1=1 --'
    result = recall_memory(malicious_query)

    assert "Hippocampus recall error" not in result
