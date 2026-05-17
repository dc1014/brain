from System.organs.vestibular import create_snapshot, restore_balance


def test_vestibular_atomic_rollback(monkeypatch, tmp_path):
    # Setup safe sandbox
    monkeypatch.setattr("System.organs.vestibular.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "System.organs.vestibular.VESTIBULAR_DIR", tmp_path / "Vestibular"
    )
    monkeypatch.setattr(
        "System.organs.vestibular.LEDGER_PATH", tmp_path / "Vestibular" / "ledger.json"
    )

    # 1. Create a dummy file
    dummy_file = tmp_path / "main.py"
    dummy_file.write_text("print('original state')")

    # 2. Take a snapshot
    create_snapshot("main.py")

    # 3. Simulate an AI mangling the file
    dummy_file.write_text("print('AI HALLUCINATED AND DELETED EVERYTHING')")

    # 4. Trigger the reflex
    restore_balance()

    # 5. Assert the file is back to normal
    assert dummy_file.read_text() == "print('original state')", (
        "Vestibular system failed to catch the fall!"
    )
