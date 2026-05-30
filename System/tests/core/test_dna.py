import json
from System.core.dna import _compute_dna_hash, _apply_cognitive_pruning


def test_compute_dna_hash(tmp_path, mocker):
    """Proves the hash correctly calculates composite checksums of active config files."""
    mocker.patch("System.core.dna.ROOT_DIR", tmp_path)

    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)

    # Hydrate dummy files
    (config_dir / "system.yaml").write_text("system: active")
    (config_dir / "agents.yaml").write_text("agents: active")

    # The hash should resolve deterministically based on file contents
    h1 = _compute_dna_hash()
    assert len(h1) > 0

    # Changing a file should alter the hash
    (config_dir / "system.yaml").write_text("system: modified")
    h2 = _compute_dna_hash()
    assert h1 != h2


def test_apply_cognitive_pruning_removes_disabled_tools(tmp_path, mocker):
    """Proves the feature flag registry correctly strips disabled tools from the LLM context."""
    mocker.patch("System.core.dna.ROOT_DIR", tmp_path)

    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)

    # 1. Setup a mocked features.json where vision and audio are explicitly disabled
    features_data = {"vision": {"enabled": False}, "audio": {"enabled": False}}
    (config_dir / "features.json").write_text(
        json.dumps(features_data), encoding="utf-8"
    )

    # 2. Setup a dummy tools configuration representing a loaded tools.yaml
    dummy_config = {
        "tools": {
            "base": [
                {"function": {"name": "read_safe_file"}},
                {"function": {"name": "speak"}},  # This should be pruned
            ],
            "execute": [
                {"function": {"name": "analyze_audio"}},  # This should be pruned
            ],
            "vision": [  # This entire group should be pruned
                {"function": {"name": "analyze_image"}},
                {"function": {"name": "capture_screenshot"}},
            ],
        }
    }

    # 3. Apply the pruning
    pruned_config = _apply_cognitive_pruning(dummy_config)

    # 4. Assertions
    assert "vision" not in pruned_config["tools"], (
        "Entire vision group should be removed"
    )

    base_tool_names = [t["function"]["name"] for t in pruned_config["tools"]["base"]]
    assert "read_safe_file" in base_tool_names, "Standard tools must remain untouched"
    assert "speak" not in base_tool_names, (
        "'speak' tool must be pruned because audio is disabled"
    )

    execute_tool_names = [
        t["function"]["name"] for t in pruned_config["tools"]["execute"]
    ]
    assert "analyze_audio" not in execute_tool_names, (
        "'analyze_audio' tool must be pruned"
    )


def test_apply_cognitive_pruning_ignores_enabled_tools(tmp_path, mocker):
    """Proves that enabled features retain their tools in the LLM context."""
    mocker.patch("System.core.dna.ROOT_DIR", tmp_path)

    config_dir = tmp_path / "System" / "config"
    config_dir.mkdir(parents=True)

    # Vision is ENABLED
    features_data = {"vision": {"enabled": True}}
    (config_dir / "features.json").write_text(
        json.dumps(features_data), encoding="utf-8"
    )

    dummy_config = {"tools": {"vision": [{"function": {"name": "analyze_image"}}]}}

    pruned_config = _apply_cognitive_pruning(dummy_config)
    assert "vision" in pruned_config["tools"]
    assert len(pruned_config["tools"]["vision"]) == 1
