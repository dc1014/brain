from System.neuroanatomy.pathways.corpus_callosum import route_hemisphere


def test_corpus_callosum_disabled(monkeypatch):
    monkeypatch.setenv("USE_LOCAL_SLM", "false")
    assert route_hemisphere("AMYGDALA", "gpt-4o-mini") == "gpt-4o-mini"


def test_corpus_callosum_left_brain_expansion(monkeypatch):
    monkeypatch.setenv("USE_LOCAL_SLM", "true")
    monkeypatch.setenv("LOCAL_MODEL_NAME", "ollama/llama3")

    # Core Operations
    assert route_hemisphere("WORKSPACE", "gpt-4o") == "ollama/llama3"
    assert route_hemisphere("DISPATCHER", "gpt-4o") == "ollama/llama3"

    # High-Privacy Operations (New!)
    assert route_hemisphere("AMYGDALA", "gpt-4o-mini") == "ollama/llama3"
    assert route_hemisphere("MEMORY", "claude-3-haiku") == "ollama/llama3"
    assert route_hemisphere("SENSE", "gemini-flash") == "ollama/llama3"


def test_corpus_callosum_right_brain_coding(monkeypatch):
    monkeypatch.setenv("USE_LOCAL_SLM", "true")
    monkeypatch.setenv("LOCAL_MODEL_NAME", "ollama/llama3")

    # Complex tasks MUST stay Right Brain
    assert route_hemisphere("FORGE", "gpt-4o") == "gpt-4o"
    assert route_hemisphere("SWARM", "claude-3-5-sonnet") == "claude-3-5-sonnet"
