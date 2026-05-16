from System.neuroanatomy.systemic.enteric import save_gut_reaction, get_gut_reaction


def test_enteric_gut_reaction(monkeypatch, tmp_path):
    """Proves the Enteric Nervous System caches and retrieves routing reflexes."""

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.enteric.GUT_MEMORY_FILE",
        tmp_path / "gut_memory.json",
    )

    assert get_gut_reaction("Run my tests") is None

    # Use WORKSPACE because FORGE is now forbidden from being cached!
    save_gut_reaction("Run my python tests", True, "Safe task", "WORKSPACE", "STUDIO")

    exact = get_gut_reaction("run my python tests")
    assert exact is not None


def test_enteric_forbids_dangerous_routes(monkeypatch, tmp_path):
    import json

    mock_file = tmp_path / "gut_memory.json"
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.enteric.GUT_MEMORY_FILE", mock_file
    )
    monkeypatch.setattr("System.neuroanatomy.systemic.enteric.ROOT_DIR", tmp_path)

    cache = {
        "deploy to staging": {
            "is_valid": True,
            "reason": "OK",
            "route_type": "FORGE",
            "domain": "STUDIO",
        }
    }
    mock_file.parent.mkdir(parents=True, exist_ok=True)  # <-- Fixed FileExistsError
    with open(mock_file, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    assert get_gut_reaction("deploy to staging") is None


def test_enteric_cerebellum_reflex_interception(monkeypatch, tmp_path):
    """Proves the Enteric system can intercept a natural language prompt and fire an engram."""
    from System.neuroanatomy.systemic.enteric import trigger_cerebellum_reflex

    monkeypatch.setattr("System.neuroanatomy.systemic.enteric.ROOT_DIR", tmp_path)

    engram_dir = tmp_path / "Meta" / "Engrams"
    engram_dir.mkdir(parents=True)

    # Generate a dummy engram
    engram_file = engram_dir / "init_vite_react.json"
    engram_file.write_text(
        '{"description": "Scaffolds a Vite app", "commands": []}', encoding="utf-8"
    )

    # Mock the execute tool so we don't actually run shell commands in the test loop
    from System.core.schemas import ExecutionResult

    monkeypatch.setattr(
        "System.tools.execute_engram",
        lambda name, target: ExecutionResult(success=True, output="Executed Engram!"),
    )

    # Test 1: Match by spaced name + dynamic folder path extraction
    res = trigger_cerebellum_reflex("Please init vite react in Studio/TestApp")
    assert res is not None
    assert res[0] is False  # Must be False to abort the LLM Pipeline!
    assert "ENTERIC REFLEX SUCCESS" in res[1]

    # Test 2: Unrelated prompt should be ignored by the Gut
    res_none = trigger_cerebellum_reflex("Please build a python server")
    assert res_none is None
