# --- System/tests/autonomic/test_interoception.py ---
import json
from datetime import datetime
from System.neuroanatomy.autonomic.interoception import (
    get_token_budget,
    get_current_metabolism,
    validate_metabolic_clearance,
)


def test_get_token_budget_dynamic_parsing(monkeypatch, tmp_path):
    """Proves the system dynamically reads the custom budget or defaults safely."""
    config_file = tmp_path / "system.yaml"
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.interoception.SYSTEM_CONFIG_PATH", config_file
    )

    # Test 1: File missing (Default Fallback)
    assert get_token_budget() == 500000

    # Test 2: Custom Value
    config_file.write_text("max_daily_token_budget: 1250\n", encoding="utf-8")
    assert get_token_budget() == 1250


def test_metabolic_clearance_gate(monkeypatch, tmp_path):
    """Proves the gate accurately denies dispatch if the budget is breached."""
    config_file = tmp_path / "system.yaml"
    metabolism_file = tmp_path / "metabolism.json"

    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.interoception.SYSTEM_CONFIG_PATH", config_file
    )
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.interoception.METABOLISM_FILE", metabolism_file
    )
    monkeypatch.setattr("System.neuroanatomy.autonomic.interoception.LOG_DIR", tmp_path)

    # Set strict test budget
    config_file.write_text("max_daily_token_budget: 100\n", encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # State 1: Under budget
    metabolism_file.write_text(
        json.dumps({"date": today, "tokens_burned": 50, "exhausted": False}),
        encoding="utf-8",
    )
    is_clear, msg = validate_metabolic_clearance()
    assert is_clear is True
    assert "approved" in msg

    # State 2: Over budget
    metabolism_file.write_text(
        json.dumps({"date": today, "tokens_burned": 150, "exhausted": True}),
        encoding="utf-8",
    )
    is_clear, msg = validate_metabolic_clearance()
    assert is_clear is False
    assert "exhausted" in msg.lower()


def test_daily_metabolism_resets_on_new_day(monkeypatch, tmp_path):
    """Proves that a sleep cycle (date change) flushes the metabolic memory."""
    metabolism_file = tmp_path / "metabolism.json"
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.interoception.METABOLISM_FILE", metabolism_file
    )

    # Hardcode a fake "yesterday" state
    metabolism_file.write_text(
        json.dumps({"date": "1999-12-31", "tokens_burned": 999999, "exhausted": True}),
        encoding="utf-8",
    )

    data = get_current_metabolism()
    assert data["tokens_burned"] == 0
    assert data["exhausted"] is False
