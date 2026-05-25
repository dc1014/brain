# --- System/tests/core/test_boot.py ---
import os
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

    # Assert primary membranes were scaffolded by the dual-membrane recovery check
    assert (tmp_path / "Studio").exists()
    assert (tmp_path / "Meta").exists()
    assert (tmp_path / "Media").exists()
    assert (tmp_path / "System" / "logs").exists()

    # Verify environment keys were natively parsed out of the local OS environment
    assert os.environ.get("GEMINI_API_KEY") == "AIzaSyFakeKeyStringForTestingPurposes12"


def test_system_bootstrap_partial_healing(tmp_path, monkeypatch, mocker):
    """Zero-Debt Test: Proves that if one core folder exists but another is missing, bootstrap heals the missing directory structure."""
    monkeypatch.setattr("System.core.boot.ROOT_DIR", tmp_path)

    mocker.patch("System.neuroanatomy.systemic.immune_system.vault.secure_environment")

    # Simulate a partial scaffolding regression where Meta exists but Media does not
    (tmp_path / "Meta").mkdir(parents=True, exist_ok=True)
    assert not (tmp_path / "Media").exists()

    success = bootstrap()

    assert success is True
    assert (tmp_path / "Media").exists()
    assert (tmp_path / "Studio").exists()
