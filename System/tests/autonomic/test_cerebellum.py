from System.neuroanatomy.autonomic.cerebellum import (
    create_engram,
    execute_engram,
    list_engrams,
)
from System.core.schemas import ExecutionResult


def test_cerebellum_muscle_memory(monkeypatch, tmp_path):
    """Zero-Debt Test: Proves the Cerebellum can save, list, and execute procedural shell scripts safely."""

    # 1. Sandbox the Cerebellum
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.ENGRAM_DIR", tmp_path / "Engrams"
    )

    # 2. Test Consolidation (Saving)
    create_res = create_engram(
        "test_setup", "Sets up a test project", ["npm init -y", "npm install react"]
    )
    assert "successfully saved" in create_res

    # 3. Test Recall (Listing)
    list_res = list_engrams()
    assert "test_setup" in list_res
    assert "Sets up a test project" in list_res

    # 4. Mock the Motor Cortex to succeed
    def mock_execute(cmd, d):
        return ExecutionResult(success=True, output=f"Ran {cmd}", block_reason="")

    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.execute_command", mock_execute
    )

    # 5. Test Reflex Execution
    exec_res = execute_engram("test_setup", "Studio")
    assert "executed flawlessly" in exec_res
    assert "SUCCESS: npm init -y" in exec_res
