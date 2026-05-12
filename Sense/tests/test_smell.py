from Sense.receptors.smell import smell_environment


def test_sniff_environment_raw(tmp_path):
    """Proves the Nose extracts raw rot data correctly without touching memory."""
    studio = tmp_path / "Studio"
    studio.mkdir()

    (studio / "empty.md").write_text("")
    (studio / "good.md").write_text("I link to [[missing|alias]].")
    (studio / "dead.jpg").write_bytes(b"")

    data = smell_environment(str(studio))

    assert "empty.md" in data["empty_files"][0]
    assert "Missing: [[missing.md]]" in data["broken_links"][0]
    assert "dead.jpg" in data["dead_media"][0]
