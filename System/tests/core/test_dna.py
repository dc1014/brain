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
    """Proves the DNA factory successfully loads and caches the split configuration layout."""
    monkeypatch.setattr("System.core.dna.ROOT_DIR", tmp_path)
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)

    # Hydrate configuration placeholders matching the files
    (config_dir / "system.yaml").write_text("models: {}", encoding="utf-8")
    (config_dir / "agents.yaml").write_text(
        "agents:\n  test_agent:\n    name: Test Node", encoding="utf-8"
    )
    (config_dir / "tools.yaml").write_text("tools: {}", encoding="utf-8")

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
    """Proves the DNA factory returns cached config records on matching hashes."""
    monkeypatch.setattr("System.core.dna.ROOT_DIR", tmp_path)
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "system.yaml").write_text("models: {}", encoding="utf-8")
    (config_dir / "agents.yaml").write_text("agents: {}", encoding="utf-8")
    (config_dir / "tools.yaml").write_text("tools: {}", encoding="utf-8")

    mock_validator = mocker.patch(
        "System.core.config_proofreader.proofread_global_config"
    )
    mock_validator.return_value.model_dump.return_value = {"cached": True}

    get_dna_config()
    assert mock_validator.call_count == 1

    get_dna_config()
    assert mock_validator.call_count == 1  # Bypassed on match!


def test_dna_hot_reload_mutation(monkeypatch, tmp_path, mocker):
    """Proves that a mutation across any target file triggers hot-reloading."""
    monkeypatch.setattr("System.core.dna.ROOT_DIR", tmp_path)
    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)

    agents_file = config_dir / "agents.yaml"
    (config_dir / "system.yaml").write_text("models: {}", encoding="utf-8")
    agents_file.write_text("version: 1", encoding="utf-8")
    (config_dir / "tools.yaml").write_text("tools: {}", encoding="utf-8")

    mock_validator = mocker.patch(
        "System.core.config_proofreader.proofread_global_config"
    )

    mock_validator.return_value.model_dump.return_value = {"version": 1}
    get_dna_config()
    assert mock_validator.call_count == 1

    agents_file.write_text("version: 2", encoding="utf-8")
    mock_validator.return_value.model_dump.return_value = {"version": 2}

    result = get_dna_config()
    assert result == {"version": 2}
    assert mock_validator.call_count == 2
