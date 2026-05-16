from System.neuroanatomy.limbic.episodic import encode_episode, recall_recent_episodes


def test_episodic_memory_cycle(tmp_path, monkeypatch):
    """Proves the brain can encode and recall autobiographical episodes."""
    mock_file = tmp_path / "autobiography.jsonl"
    monkeypatch.setattr("System.neuroanatomy.limbic.episodic.MEMORY_FILE", mock_file)

    # 1. Brain starts with no memory
    assert "No previous life experiences" in recall_recent_episodes()

    # 2. Brain encodes an experience
    encode_episode("Build App", ["Write code", "Test code"], "Success")

    # 3. Brain recalls the experience
    recalled = recall_recent_episodes()
    assert "GOAL: Build App" in recalled
    assert "OUTCOME: Success" in recalled
    assert "Write code, Test code" in recalled
