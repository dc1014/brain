from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere


def test_route_hemisphere_local_disabled(monkeypatch):
    """Proves the bridge respects the config and stays in the Cloud when local is disabled."""
    monkeypatch.setenv("USE_LOCAL_SLM", "false")

    assert route_hemisphere("DISPATCHER", "gpt-4o") == "gpt-4o"
    assert route_hemisphere("FORGE", "gpt-4o") == "gpt-4o"


def test_route_hemisphere_local_enabled_left_brain(monkeypatch):
    """Proves the bridge routes background tasks to the local SLM when enabled."""
    monkeypatch.setenv("USE_LOCAL_SLM", "true")
    monkeypatch.setenv("LOCAL_MODEL_NAME", "ollama/llama3.2")

    assert route_hemisphere("DISPATCHER", "gpt-4o") == "ollama/llama3.2"
    assert route_hemisphere("SUBCONSCIOUS_DAYDREAM", "gpt-4o") == "ollama/llama3.2"
    assert route_hemisphere("WERNICKE", "gpt-4o") == "ollama/llama3.2"


def test_route_hemisphere_local_enabled_right_brain(monkeypatch):
    """Proves the bridge refuses to route complex tasks to the SLM, even if local is enabled."""
    monkeypatch.setenv("USE_LOCAL_SLM", "true")

    assert route_hemisphere("FORGE", "gpt-4o") == "gpt-4o"
    assert route_hemisphere("SWARM", "gpt-4o") == "gpt-4o"
