from System.organs.enteric import save_gut_reaction, get_gut_reaction


def test_enteric_gut_reaction(monkeypatch, tmp_path):
    """Proves the Enteric Nervous System caches and retrieves routing reflexes."""

    # Sandbox the cache file
    monkeypatch.setattr(
        "System.organs.enteric.GUT_MEMORY_FILE", tmp_path / "gut_memory.json"
    )

    # 1. Initially empty
    assert get_gut_reaction("Run my tests") is None

    # 2. Save a reaction (Mocking a successful LLM Dispatcher route)
    save_gut_reaction("Run my python tests", True, "Safe task", "FORGE", "STUDIO")

    # 3. Test exact match
    exact = get_gut_reaction("run my python tests")
    assert exact is not None
    assert exact[2] == "FORGE"

    # 4. Test fuzzy match (missing a word, but >90% similar)
    fuzzy = get_gut_reaction("run my python test")  # missing the 's'
    assert fuzzy is not None
    assert fuzzy[2] == "FORGE"

    # 5. Test complete miss
    miss = get_gut_reaction("Write a new react app")
    assert miss is None
