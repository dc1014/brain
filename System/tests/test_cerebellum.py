def test_cerebellum_muscle_memory(monkeypatch, tmp_path):
    """Proves the Cerebellum can save, list, and index procedural muscle memory."""
    from System.organs.cerebellum import save_engram, list_engrams

    # 1. Sandbox the Cerebellum
    root = tmp_path
    engram_dir = root / "System" / "engrams"
    index_file = engram_dir / "index.json"

    monkeypatch.setattr("System.organs.cerebellum.ROOT_DIR", root)
    monkeypatch.setattr("System.organs.cerebellum.ENGRAM_DIR", engram_dir)
    monkeypatch.setattr("System.organs.cerebellum.INDEX_FILE", index_file)

    # 2. Save an Engram
    result = save_engram(
        "bootstrap_node", "Creates a basic package.json", "npm init -y\nmkdir src"
    )
    assert "permanently saved" in result

    # 3. Verify Files Created
    assert index_file.exists()
    script_path = engram_dir / "bootstrap_node.sh"
    assert script_path.exists()

    # 4. Verify Unix LF normalization (Zero Debt)
    script_content = script_path.read_text(encoding="utf-8")
    assert "npm init -y\nmkdir src" in script_content
    assert "\r\n" not in script_content

    # 5. List Engrams
    available = list_engrams()
    assert "bootstrap_node" in available
    assert "Creates a basic package.json" in available
