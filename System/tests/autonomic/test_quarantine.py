from System.neuroanatomy.autonomic.cerebellum import CerebellarCompiler


def test_quarantine_receives_engram(tmp_path, monkeypatch):
    """Proves the Exocortex correctly isolates inbound code."""
    monkeypatch.setattr("System.neuroanatomy.autonomic.cerebellum.ENGRAM_DIR", tmp_path)
    monkeypatch.setattr("System.neuroanatomy.autonomic.cerebellum.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.QUARANTINE_DIR",
        tmp_path / "quarantine",
    )

    compiler = CerebellarCompiler()
    response = compiler.quarantine_external_engram("hack_node", "print('hello')")

    assert "201 Created" in response
    assert (tmp_path / "quarantine" / "hack_node.py").exists()


def test_quarantine_assimilation_security_block(tmp_path, monkeypatch):
    """Proves the Spinal AST scanner catches malicious payloads and destroys them."""
    quarantine_dir = tmp_path / "quarantine"
    quarantine_dir.mkdir(parents=True)
    monkeypatch.setattr("System.neuroanatomy.autonomic.cerebellum.ENGRAM_DIR", tmp_path)
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.QUARANTINE_DIR", quarantine_dir
    )

    # Write a malicious quarantined file
    (quarantine_dir / "bad_code.py").write_text(
        "import os\nos.system('rm -rf /')", encoding="utf-8"
    )

    compiler = CerebellarCompiler()
    success, msg = compiler.assimilate_engram("bad_code")

    assert not success
    assert "Lethal call 'system'" in msg
    assert not (quarantine_dir / "bad_code.py").exists()  # Verifies destruction


def test_quarantine_assimilation_success(tmp_path, monkeypatch):
    """Proves safe engrams are successfully moved to active memory."""
    quarantine_dir = tmp_path / "quarantine"
    quarantine_dir.mkdir(parents=True)
    monkeypatch.setattr("System.neuroanatomy.autonomic.cerebellum.ENGRAM_DIR", tmp_path)
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.QUARANTINE_DIR", quarantine_dir
    )

    (quarantine_dir / "good_code.py").write_text("print('I am safe')", encoding="utf-8")

    compiler = CerebellarCompiler()
    success, msg = compiler.assimilate_engram("good_code")

    assert success
    assert (tmp_path / "good_code.py").exists()
