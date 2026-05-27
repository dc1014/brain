from System.tools.context_archaeology import analyze_context, write_report


def test_context_archaeology_finds_hidden_leverage(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "launch.md").write_text(
        "Show HN launch needs a public demo artifact and reviewer trust.",
        encoding="utf-8",
    )
    (vault / "meeting.md").write_text(
        "Client meeting decisions need owner action follow-up and a brief.",
        encoding="utf-8",
    )

    report = analyze_context(vault, goal="Show HN")

    assert report.files_scanned == 2
    assert report.top_themes
    assert "artifact" in report.to_markdown()
    assert "Show HN" in report.to_markdown()


def test_context_archaeology_writes_markdown_report(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "wedge.md").write_text(
        "A repeatable leverage opportunity should become a playbook artifact.",
        encoding="utf-8",
    )
    output = tmp_path / "brief.md"

    written = write_report(analyze_context(vault), output)

    assert written == output
    assert "CoreTex Context Archaeology Brief" in output.read_text(encoding="utf-8")
