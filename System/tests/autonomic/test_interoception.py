from System.neuroanatomy.autonomic.interoception import (
    log_metabolism,
    check_energy_levels,
    DAILY_TOKEN_LIMIT,
)


def test_metabolism_tracking(monkeypatch, tmp_path):
    """Proves the Vagus nerve correctly tracks token burn and triggers exhaustion."""
    # 1. Sandbox the file system
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.interoception.METABOLISM_FILE",
        tmp_path / "metabolism.json",
    )
    monkeypatch.setattr("System.neuroanatomy.autonomic.interoception.LOG_DIR", tmp_path)

    # 2. Initially zero
    is_exhausted, tokens = check_energy_levels()
    assert tokens == 0
    assert is_exhausted is False

    # 3. Burn some calories
    log_metabolism(1000)
    is_exhausted, tokens = check_energy_levels()
    assert tokens == 1000
    assert is_exhausted is False

    # 4. Trigger Exhaustion
    log_metabolism(DAILY_TOKEN_LIMIT + 5000)
    is_exhausted, tokens = check_energy_levels()
    assert tokens > DAILY_TOKEN_LIMIT
    assert is_exhausted is True
