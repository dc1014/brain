from System.neuroanatomy.sensory.olfactory import process_scent_profile
from System.tools import delete_safe_file


def test_delete_safe_file_lysosome(tmp_path, monkeypatch):
    monkeypatch.setattr("System.tools.file_system.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "System.tools.file_system.is_safe_path", lambda x, require_write=False: True
    )

    test_file = tmp_path / "Personal" / "bad_note.md"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("Rotting thought.")

    result = delete_safe_file("Personal/bad_note.md")

    assert "SUCCESS" in result
    assert not test_file.exists()
    assert (tmp_path / ".trash" / "manifest.jsonl").exists()


def test_process_scent_profile(tmp_path, monkeypatch):
    monkeypatch.setattr("System.neuroanatomy.sensory.olfactory.ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        "Sense.receptors.smell.subprocess.run",
        lambda *args, **kwargs: type("Mock", (), {"returncode": 0})(),
    )

    studio = tmp_path / "Studio"
    studio.mkdir()
    (studio / "empty.md").write_text("")

    report = process_scent_profile("Studio")  # <--- FIX

    assert "status='anomalies_detected'" in report
    assert "empty.md" in report


def test_olfactory_smell_broken_links_and_empty(tmp_path, monkeypatch):
    """Proves the Olfactory Bulb detects empty files and broken [[wikilinks]]."""
    monkeypatch.setattr("System.neuroanatomy.sensory.olfactory.ROOT_DIR", tmp_path)

    studio = tmp_path / "Studio"
    studio.mkdir()

    (studio / "empty.md").write_text("")
    (studio / "good.md").write_text("I link to [[existing]] and [[missing|alias]].")
    (studio / "existing.md").write_text("I am the existing file.")

    report = process_scent_profile("Studio")

    assert "status='anomalies_detected'" in report
    assert "empty.md" in report
    assert "Missing: [[missing.md]]" in report
    assert "existing.md" not in report  # It shouldn't flag the good link!
