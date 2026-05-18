from System.neuroanatomy.systemic.endocrine import EndocrineSystem, get_resolved_model


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


def test_endocrine_model_downgrade_under_stress(monkeypatch, tmp_path, mocker):
    """Proves the Endocrine system overrides premium models with efficiency models during exhaustion."""
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.endocrine.ENDOCRINE_FILE",
        tmp_path / "humoral.json",
    )

    # 1. Mock the DNA configuration
    mocker.patch(
        "System.neuroanatomy.cortical.prefrontal.get_dna_config",
        {
            "models": {
                "premium_model": "openai/gpt-4o",
                "gpt_mini": "openai/gpt-4o-mini",
            }
        },
    )

    # 2. Mock the Immune Vault
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_api_key_for_model",
        return_value="sk-fake",
    )

    # 3. Request a premium model while the system is EXHAUSTED
    # This should automatically trigger secrete("cortisol") and force a downgrade
    system = EndocrineSystem()
    system.secrete("cortisol", 1.0)  # Pre-load the stress
    resolved = get_resolved_model("premium_model", is_exhausted=True)

    # 4. Strict Validation
    assert resolved == "openai/gpt-4o-mini"


def test_endocrine_maintains_model_when_healthy(monkeypatch, tmp_path, mocker):
    """Proves the Endocrine system allows premium models when healthy."""
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.endocrine.ENDOCRINE_FILE",
        tmp_path / "humoral.json",
    )

    mocker.patch(
        "System.neuroanatomy.systemic.endocrine.get_dna_config",
        return_value={
            "models": {
                "premium_model": "openai/gpt-4o",
                "gpt_mini": "openai/gpt-4o-mini",
            }
        },
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_api_key_for_model",
        return_value="sk-fake",
    )

    # Baseline health
    resolved = get_resolved_model("premium_model", is_exhausted=False)
    assert resolved == "openai/gpt-4o"
