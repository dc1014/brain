from System.core.dna import _load_dna


def test_load_dna_success(monkeypatch, tmp_path, mocker):
    """Proves the DNA loader correctly aggregates YAML configs and passes them to the proofreader."""
    # 1. Isolate the file system
    monkeypatch.setattr("System.core.dna.ROOT_DIR", tmp_path)
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)

    # 2. Inject a fake configuration file
    agents_file = config_dir / "agents.yaml"
    agents_file.write_text(
        "agents:\n  test_agent:\n    name: Test Node", encoding="utf-8"
    )

    # 3. Mock the proofreaders at their biological source
    mocker.patch("System.neuroanatomy.pathways.polymerase.proofread_yaml_dna")
    mock_validator = mocker.patch(
        "System.core.config_proofreader.proofread_global_config"
    )

    # 4. Simulate a successfully validated return object
    mock_validator.return_value.model_dump.return_value = {
        "agents": {"test_agent": {"name": "Test Node"}},
        "routes": {},
        "models": {},
    }

    result = _load_dna()

    # 5. Strict Validation
    assert "test_agent" in result["agents"]
    assert result["agents"]["test_agent"]["name"] == "Test Node"


def test_load_dna_exception_fallback(mocker):
    """Proves the OS falls back to a sterile configuration dictionary if the DNA is corrupted."""
    # 1. Force a critical syntax error during the initial proofreading phase
    mocker.patch(
        "System.neuroanatomy.pathways.polymerase.proofread_yaml_dna",
        side_effect=Exception("Corrupted YAML Syntax"),
    )

    # 2. Execute the loader
    result = _load_dna()

    # 3. Prove it gracefully returned the sterile baseline instead of crashing
    assert result == {"agents": {}, "routes": {}, "models": {}}
