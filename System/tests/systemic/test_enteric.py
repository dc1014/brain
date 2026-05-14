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
