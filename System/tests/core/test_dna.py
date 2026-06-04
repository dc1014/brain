from System.core.dna import get_dna_config, _hash_directory


def test_dna_hash_directory(tmp_path, mocker):
    """Proves the directory hash correctly detects file changes."""
    mocker.patch("System.core.dna.AGENTS_DIR", tmp_path)

    # Create an agent
    agent_file = tmp_path / "test_agent.md"
    agent_file.write_text("---\nname: Test\n---\nBody", encoding="utf-8")

    h1 = _hash_directory(tmp_path)
    assert len(h1) > 0

    # Modify the agent
    agent_file.write_text("---\nname: Test2\n---\nBody2", encoding="utf-8")
    h2 = _hash_directory(tmp_path)

    assert h1 != h2


def test_dna_loader_merges_data(mocker):
    """Proves the DNA config returns the required system structure."""
    # We mock out the hash to prevent actual disk reads during unit test
    mocker.patch("System.core.dna._hash_directory", return_value="12345")

    config = get_dna_config(force_reload=True)

    # Ensure our major dictionaries exist
    assert "routes" in config
    assert "tools" in config
    assert "agents" in config
    assert "models" in config
