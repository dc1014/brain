def test_show_hn_demo_writes_actionable_checklist(monkeypatch, tmp_path):
    import scripts.show_hn_demo as demo

    fixture = tmp_path / "examples" / "show-hn-mini-project"
    fixture.mkdir(parents=True)
    (fixture / "README.md").write_text(
        "The quickstart should be copy/pasteable from a fresh clone.",
        encoding="utf-8",
    )
    (fixture / "error.log").write_text(
        "WARN deno not found in PATH\nERROR Permission denied: ./ctx\n",
        encoding="utf-8",
    )
    out = tmp_path / "Professional" / "show-hn-demo-checklist.md"

    monkeypatch.setattr(demo, "ROOT", tmp_path)
    monkeypatch.setattr(demo, "FIXTURE", fixture)
    monkeypatch.setattr(demo, "OUT", out)

    assert demo.main() == 0
    text = out.read_text(encoding="utf-8")
    assert "executable" in text
    assert "Deno" in text
    assert "copy/pasteable" in text
    assert "secrets" in text
