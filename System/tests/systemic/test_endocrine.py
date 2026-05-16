from System.neuroanatomy.systemic.endocrine import EndocrineSystem


def test_endocrine_secretion_and_clamping(tmp_path, monkeypatch):
    """Proves the humoral state acts as a continuous float vector safely clamped at 1.0."""
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.endocrine.ENDOCRINE_FILE",
        tmp_path / "humoral.json",
    )

    system = EndocrineSystem()

    # Secrete beyond biological limits
    system.secrete("adrenaline", 2.5)
    system.secrete("cortisol", 0.8)

    vector = system.get_humoral_vector()

    assert vector["adrenaline"] == 1.0  # Clamped
    assert vector["cortisol"] == 0.8
    assert vector["melatonin"] == 0.0


def test_endocrine_metabolism(tmp_path, monkeypatch):
    """Proves hormones decay toward homeostasis over time."""
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.endocrine.ENDOCRINE_FILE",
        tmp_path / "humoral.json",
    )

    system = EndocrineSystem()
    system.secrete("cortisol", 1.0)
    system.secrete("dopamine", -0.5)  # Zero it out

    system.metabolize()
    vector = system.get_humoral_vector()

    assert vector["cortisol"] == 0.95  # Decayed by 0.05
    assert vector["dopamine"] > 0.0  # Seeking 0.3 baseline


def test_llm_humoral_modulation(mocker):
    """Proves the bloodstream mathematically alters the LLM parameters."""
    mock_vector = {
        "cortisol": 0.9,
        "dopamine": 0.0,
        "adrenaline": 0.8,
        "melatonin": 0.0,
    }
    mocker.patch(
        "System.neuroanatomy.systemic.endocrine.EndocrineSystem.get_humoral_vector",
        return_value=mock_vector,
    )

    # Mock the AGENT_CONFIG to test Cortisol fallback
    mocker.patch("System.runtime.AGENT_CONFIG", {"models": {"fast": "cheap-model"}})

    from System.llm import apply_humoral_modulation

    mod_model, mod_temp, mod_tokens = apply_humoral_modulation("heavy-model")

    assert mod_model == "cheap-model"  # Cortisol forced the fallback
    assert mod_temp < 0.2  # High Cortisol + No Dopamine = Cold/Deterministic
    assert mod_tokens < 3000  # Adrenaline restricted verbosity
