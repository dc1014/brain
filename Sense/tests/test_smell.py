from Sense.receptors.smell import smell_environment


def test_smell_environment_advanced(tmp_path):
    studio = tmp_path / "Studio"
    studio.mkdir()

    # 1. Toxins & Cognitive Stagnation
    (studio / "bad_thoughts.md").write_text(
        "TODO: fix this\nTODO: a\nTODO: b\nTODO: c\nTODO: d\nTODO: e\nMy key is sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890ABCD"
    )

    # 2. Duplicates
    (studio / "image1.jpg").write_bytes(b"SAME_DATA")
    (studio / "image2.jpg").write_bytes(b"SAME_DATA")

    # 3. Orphaned Media vs Linked Media
    (studio / "orphaned.png").write_bytes(b"IMG_DATA")
    (studio / "linked.png").write_bytes(b"IMG_DATA")
    (studio / "note.md").write_text("Look at this ![[linked.png]]")

    # 4. Digital Dust
    (studio / ".DS_Store").write_bytes(b"")
    (studio / "old_code.bak").write_text("backup")

    # 5. Git Conflicts
    (studio / "conflict.md").write_text(
        "<<<<<<< HEAD\nMy version\n=======\nTheir version\n>>>>>>> branch"
    )

    # 6. Structural Bleed
    (studio / "unclosed.md").write_text(
        "---\ntags: [test]\n\n# Header\nForgot to close YAML!"
    )

    data = smell_environment(str(studio))

    # Assertions
    assert "bad_thoughts.md" in data["toxic_rot"][0]
    assert "bad_thoughts.md" in data["cognitive_rot"][0]
    assert any("image1.jpg" in d for d in data["duplicate_files"])
    assert any("image2.jpg" in d for d in data["duplicate_files"])

    assert any("orphaned.png" in d for d in data["orphaned_media"])
    assert not any("linked.png" in d for d in data["orphaned_media"])

    assert any(".DS_Store" in d for d in data["digital_dust"])
    assert any("old_code.bak" in d for d in data["digital_dust"])

    assert "conflict.md" in data["git_conflict_rot"][0]
    assert "unclosed.md" in data["structural_rot"][0]
