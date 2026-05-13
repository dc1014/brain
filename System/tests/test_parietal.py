from System.organs.parietal import generate_spatial_map


def test_parietal_code_mermaid_and_vertigo(tmp_path):
    (tmp_path / "a.py").write_text("import b")
    (tmp_path / "b.py").write_text("import a")

    mermaid_out = generate_spatial_map(str(tmp_path), "mermaid", "code")
    assert "```mermaid" in mermaid_out
    assert "--> b" in mermaid_out

    vertigo_out = generate_spatial_map(str(tmp_path), "vertigo_check", "code")
    assert "[VERTIGO DETECTED]" in vertigo_out


def test_parietal_knowledge_graph_notes(tmp_path):
    # Create fake Obsidian notes with wikilinks and aliases!
    (tmp_path / "Project Alpha.md").write_text(
        "This relates to [[Budget 2026]] and [[John Doe|Justin]]."
    )
    (tmp_path / "Budget 2026.md").write_text("Empty note.")

    # Map the thought topology
    note_graph = generate_spatial_map(str(tmp_path), "json", "notes")

    # Assert it correctly extracted the thought links, stripping the alias and extension
    assert "Project Alpha" in note_graph
    assert "Budget 2026" in note_graph
    assert "John Doe" in note_graph
    assert "Justin" not in note_graph  # Proves the alias was correctly stripped
