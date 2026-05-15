import tarfile
from System.neuroanatomy.systemic.lymphatic import flush_waste, purge_waste


def test_lymphatic_system_archives_logs_to_tarball(monkeypatch, tmp_path):
    monkeypatch.setattr("System.neuroanatomy.systemic.lymphatic.ROOT_DIR", tmp_path)

    # 1. Setup mock logs
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "agent_interactions.jsonl"
    lines = [f"Log entry {i}\n" for i in range(5)]
    log_file.write_text("".join(lines), encoding="utf-8")

    # 2. Flush
    flush_waste(max_log_lines=2)

    # 3. Assert Active Log was trimmed
    remaining_lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(remaining_lines) == 2

    # 4. Assert Tarball was created in Lymph_Nodes
    lymph_dir = tmp_path / "Meta" / "Lymph_Nodes"
    tarballs = list(lymph_dir.glob("*.tar.gz"))
    assert len(tarballs) == 1

    # 5. Assert Tarball contains the trimmed data
    with tarfile.open(tarballs[0], "r:gz") as tar:
        members = tar.getnames()
        assert any("archived_interactions" in name for name in members)


def test_lymphatic_purge_destroys_tarballs(monkeypatch, tmp_path):
    monkeypatch.setattr("System.neuroanatomy.systemic.lymphatic.ROOT_DIR", tmp_path)

    lymph_dir = tmp_path / "Meta" / "Lymph_Nodes"
    lymph_dir.mkdir(parents=True)
    fake_tar = lymph_dir / "fake.tar.gz"
    fake_tar.write_text("dummy binary data")

    purge_waste()

    assert not fake_tar.exists(), "Purge failed to destroy tarball!"


def test_lymphatic_full_flush_resets_ledger(monkeypatch, tmp_path):
    """
    Zero-Debt Test: Ensures a full flush (max_log_lines=0) completely
    clears the token ledger to reset metabolism and bypasses the Python 0-slice bug.
    """
    monkeypatch.setattr("System.neuroanatomy.systemic.lymphatic.ROOT_DIR", tmp_path)

    log_file = tmp_path / "agent_interactions.jsonl"
    # Simulate high-token metabolic waste
    lines = [
        f'{{"prompt_tokens": 100000, "completion_tokens": 50000, "entry": {i}}}\n'
        for i in range(5)
    ]
    log_file.write_text("".join(lines), encoding="utf-8")

    # Trigger full biological flush (0 lines kept)
    flush_waste(max_log_lines=0)

    # Strict Validation: The waste must be entirely eradicated
    assert not log_file.exists(), (
        "Glymphatic system failed to completely delete the token ledger!"
    )

    # Ensure it was archived safely to the Lymph Nodes
    lymph_dir = tmp_path / "Meta" / "Lymph_Nodes"
    tarballs = list(lymph_dir.glob("*.tar.gz"))
    assert len(tarballs) == 1


def test_lymphatic_full_flush_resets_metabolism(monkeypatch, tmp_path):
    """
    Zero-Debt Test: Ensures a full flush (max_log_lines=0) completely
    clears the metabolism.json state file to remove phantom fatigue.
    """
    monkeypatch.setattr("System.neuroanatomy.systemic.lymphatic.ROOT_DIR", tmp_path)

    metabolism_file = tmp_path / "metabolism.json"
    # Simulate an exhausted state
    metabolism_file.write_text(
        '{"date": "2026-05-15", "tokens_burned": 699978, "exhausted": true}',
        encoding="utf-8",
    )

    # Trigger full biological flush
    flush_waste(max_log_lines=0)

    # Strict Validation: The metabolic state must be entirely eradicated
    assert not metabolism_file.exists(), (
        "Glymphatic system failed to clear metabolism.json!"
    )
