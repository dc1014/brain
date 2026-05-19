from System.neuroanatomy.autonomic.vestibular import VestibularSystem


def test_vestibular_directory_orphan_pruning(tmp_path, monkeypatch):
    """Proves the Vestibular system obliterates newly created directories during a rollback."""
    monkeypatch.setattr("System.neuroanatomy.autonomic.vestibular.ROOT_DIR", tmp_path)
    state_file = tmp_path / "Meta" / "vestibular_state.json"
    backup_dir = tmp_path / "Meta" / "vestibular_backups"
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.vestibular.VESTIBULAR_STATE_FILE", state_file
    )
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.vestibular.BACKUP_DIR", backup_dir
    )

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").touch()

    vestibular = VestibularSystem()
    vestibular.commit_transaction()

    rogue_dir = tmp_path / "rogue_build" / "nested" / "deep"
    rogue_dir.mkdir(parents=True)
    (rogue_dir / "bad_file.txt").touch()

    monkeypatch.setattr("os.system", lambda x: None)
    vestibular.restore_balance()

    assert not (tmp_path / "rogue_build").exists()
    assert (tmp_path / "src").exists()


def test_vestibular_file_snapshot(tmp_path, monkeypatch):
    """Proves targeted file snapshots are correctly backed up and restored."""
    monkeypatch.setattr("System.neuroanatomy.autonomic.vestibular.ROOT_DIR", tmp_path)
    state_file = tmp_path / "Meta" / "vestibular_state.json"
    backup_dir = tmp_path / "Meta" / "vestibular_backups"
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.vestibular.VESTIBULAR_STATE_FILE", state_file
    )
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.vestibular.BACKUP_DIR", backup_dir
    )

    # Setup target file
    target_file = tmp_path / "test_doc.txt"
    target_file.write_text("original content", encoding="utf-8")

    vestibular = VestibularSystem()
    vestibular.commit_transaction()

    # Take targeted snapshot (as the file_system tool would)
    vestibular.snapshot_file("test_doc.txt")

    # Mutate the file
    target_file.write_text("mutated content", encoding="utf-8")
    assert target_file.read_text(encoding="utf-8") == "mutated content"

    monkeypatch.setattr("os.system", lambda x: None)

    # Execute rollback
    vestibular.restore_balance()

    # Verify file is restored perfectly
    assert target_file.read_text(encoding="utf-8") == "original content"


def test_vestibular_protects_core_files(tmp_path, monkeypatch):
    """Proves the Vestibular system does not roll back core OS files like brain.bat."""
    monkeypatch.setattr("System.neuroanatomy.autonomic.vestibular.ROOT_DIR", tmp_path)
    state_file = tmp_path / "Meta" / "vestibular_state.json"
    backup_dir = tmp_path / "Meta" / "vestibular_backups"
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.vestibular.VESTIBULAR_STATE_FILE", state_file
    )
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.vestibular.BACKUP_DIR", backup_dir
    )

    vestibular = VestibularSystem()

    # 1. Take the initial snapshot
    vestibular.commit_transaction()

    # 2. Simulate the user creating `brain.bat` AND a rogue agent creating a garbage file mid-task
    brain_bat = tmp_path / "brain.bat"
    brain_bat.write_text("echo hello", encoding="utf-8")

    rogue_file = tmp_path / "rogue.txt"
    rogue_file.touch()

    # 3. Trigger the rollback
    monkeypatch.setattr("os.system", lambda x: None)
    vestibular.restore_balance()

    # 4. Prove `brain.bat` survived the purge, but `rogue.txt` was executed!
    assert brain_bat.exists()
    assert not rogue_file.exists()
