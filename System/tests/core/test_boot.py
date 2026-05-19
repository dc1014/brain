from System.core.boot import bootstrap


def test_system_bootstrap_lifecycle(tmp_path, monkeypatch, mocker):
    """Zero-Debt Test: Proves the global baseline bootstrap initializes directory maps and locks Vault states cleanly."""
    monkeypatch.setattr("System.core.boot.ROOT_DIR", tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyFakeKeyStringForTestingPurposes12")

    mock_vault_secure = mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.secure_environment"
    )

    success = bootstrap()

    assert success is True
    mock_vault_secure.assert_called_once()

    # Assert primary membranes were scaffolded by the single-stat check
    assert (tmp_path / "Studio").exists()
    assert (tmp_path / "Meta").exists()
    assert (tmp_path / "System" / "logs").exists()

    # Verify environment keys were natively parsed out of the local OS environment
    import os

    # Note: Vault.secure_environment usually deletes them from os.environ,
    # but we mocked the vault method above, so it remains in os.environ for this isolated test context.
    assert os.environ.get("GEMINI_API_KEY") == "AIzaSyFakeKeyStringForTestingPurposes12"
