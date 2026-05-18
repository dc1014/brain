import tarfile
from System.organs.lymphatic import flush_waste, purge_waste


def test_lymphatic_system_archives_logs_to_tarball(monkeypatch, tmp_path):
    monkeypatch.setattr("System.organs.lymphatic.ROOT_DIR", tmp_path)

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
    monkeypatch.setattr("System.organs.lymphatic.ROOT_DIR", tmp_path)

    lymph_dir = tmp_path / "Meta" / "Lymph_Nodes"
    lymph_dir.mkdir(parents=True)
    fake_tar = lymph_dir / "fake.tar.gz"
    fake_tar.write_text("dummy binary data")

    purge_waste()

    assert not fake_tar.exists(), "Purge failed to destroy tarball!"
