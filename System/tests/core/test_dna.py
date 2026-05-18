import pytest
from System.core.dna import get_dna_config
import System.core.dna as dna_module


@pytest.fixture(autouse=True)
def reset_dna_cache():
    """Ensure a clean global cache state before every test."""
    dna_module._cached_config = {}
    dna_module._cached_hash = ""
    yield
    dna_module._cached_config = {}
    dna_module._cached_hash = ""


def test_dna_initial_load(monkeypatch, tmp_path, mocker):
    """Proves the DNA factory successfully loads and caches config on the first run."""
    monkeypatch.setattr("System.core.dna.ROOT_DIR", tmp_path)
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)

    agents_file = config_dir / "agents.yaml"
    agents_file.write_text(
        "agents:\n  test_agent:\n    name: Test Node", encoding="utf-8"
    )

    mocker.patch("System.neuroanatomy.pathways.polymerase.proofread_yaml_dna")
    mock_validator = mocker.patch(
        "System.core.config_proofreader.proofread_global_config"
    )

    mock_validator.return_value.model_dump.return_value = {
        "agents": {"test_agent": {"name": "Test Node"}}
    }

    result = get_dna_config()

    assert "test_agent" in result["agents"]
    assert dna_module._cached_hash != ""
    assert dna_module._cached_config == result


def test_dna_cache_hit_bypass(monkeypatch, tmp_path, mocker):
    """Proves the DNA factory returns cached memory without re-reading files if the hash matches."""
    monkeypatch.setattr("System.core.dna.ROOT_DIR", tmp_path)
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "agents.yaml").write_text("agents: {}", encoding="utf-8")

    mock_proofread = mocker.patch(
        "System.neuroanatomy.pathways.polymerase.proofread_yaml_dna"
    )
    mock_validator = mocker.patch(
        "System.core.config_proofreader.proofread_global_config"
    )
    mock_validator.return_value.model_dump.return_value = {"cached": True}

    # 1. First call loads the cache
    result1 = get_dna_config()
    assert result1 == {"cached": True}
    assert mock_proofread.call_count == 1

    # 2. Second call should instantly return the cache (proofread NOT called again)
    result2 = get_dna_config()
    assert result2 == {"cached": True}
    assert mock_proofread.call_count == 1  # Still 1! It bypassed the heavy lifting.


def test_dna_hot_reload_mutation(monkeypatch, tmp_path, mocker):
    """Proves the DNA factory detects file mutations and hot-reloads the config."""
    monkeypatch.setattr("System.core.dna.ROOT_DIR", tmp_path)
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)

    agents_file = config_dir / "agents.yaml"
    agents_file.write_text("version: 1", encoding="utf-8")

    mock_proofread = mocker.patch(
        "System.neuroanatomy.pathways.polymerase.proofread_yaml_dna"
    )
    mock_validator = mocker.patch(
        "System.core.config_proofreader.proofread_global_config"
    )

    # 1. Load initial state
    mock_validator.return_value.model_dump.return_value = {"version": 1}
    get_dna_config()
    assert mock_proofread.call_count == 1

    # 2. Mutate the file on disk!
    agents_file.write_text("version: 2", encoding="utf-8")
    mock_validator.return_value.model_dump.return_value = {"version": 2}

    # 3. Request config again. It should detect the hash change and reload!
    result = get_dna_config()
    assert result == {"version": 2}
    assert mock_proofread.call_count == 2  # Proves it ran the pipeline again!


def test_dna_exception_fallback(mocker):
    """Proves the OS falls back to a sterile configuration dictionary if the DNA is corrupted."""
    mocker.patch(
        "System.neuroanatomy.pathways.polymerase.proofread_yaml_dna",
        side_effect=Exception("Corrupted YAML Syntax"),
    )

    result = get_dna_config(force_reload=True)
    assert result == {"agents": {}, "routes": {}, "models": {}}
