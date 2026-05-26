# --- System/tests/pathways/test_corpus_callosum.py ---
from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere


def test_corpus_callosum_left_brain_routing(monkeypatch):
    """Proves analytical routes execute locally when the SLM flag is active."""
    monkeypatch.setenv("USE_LOCAL_SLM", "true")
    monkeypatch.setenv("LOCAL_MODEL_NAME", "ollama/phi4")

    # Analytical routing path (e.g. searching the workspace) should map to the local model
    assert route_hemisphere("WORKSPACE", "gpt-4o") == "ollama/phi4"

    # Subconscious background routes must map locally
    assert route_hemisphere("SUBCONSCIOUS_DAYDREAM", "gpt-4o") == "ollama/phi4"


def test_corpus_callosum_right_brain_routing(monkeypatch):
    """Proves creative/expensive routes ALWAYS bypass the local SLM."""
    monkeypatch.setenv("USE_LOCAL_SLM", "true")
    monkeypatch.setenv("LOCAL_MODEL_NAME", "ollama/phi4")

    # Creative code generation and massive swarm intelligence MUST run in the cloud
    assert route_hemisphere("CODE_GENERATION", "gpt-4o") == "gpt-4o"
    assert route_hemisphere("FORGE", "gpt-4o") == "gpt-4o"


def test_corpus_callosum_disabled_fallback(monkeypatch):
    """Proves all routes gracefully fall back to the cloud if SLMs are disabled."""
    monkeypatch.setenv("USE_LOCAL_SLM", "false")
    monkeypatch.setenv("LOCAL_MODEL_NAME", "ollama/phi4")

    # Even analytical workspace tasks stay in the cloud because the flag is false
    assert route_hemisphere("WORKSPACE", "gpt-4o") == "gpt-4o"
    assert route_hemisphere("DISPATCHER", "gpt-4o") == "gpt-4o"
