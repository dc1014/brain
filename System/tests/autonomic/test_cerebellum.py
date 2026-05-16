from System.neuroanatomy.autonomic.cerebellum import (
    create_engram,
    execute_engram,
    list_engrams,
)
from System.core.schemas import ExecutionResult


def test_cerebellum_muscle_memory(monkeypatch, tmp_path):
    """Zero-Debt Test: Proves the Cerebellum can save, list, and execute procedural shell scripts safely."""
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.ENGRAM_DIR", tmp_path / "Engrams"
    )

    create_res = create_engram("test_setup", "Sets up a test project", ["npm init -y"])
    assert "successfully saved" in create_res

    list_res = list_engrams()
    assert "test_setup" in list_res

    def mock_execute(cmd, d):
        return ExecutionResult(success=True, output=f"Ran {cmd}", block_reason="")

    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.execute_command", mock_execute
    )

    exec_res = execute_engram("test_setup", "Studio")
    assert "executed flawlessly" in exec_res


def test_cerebellum_parametric_engrams(monkeypatch, tmp_path):
    """Proves that engrams can dynamically inject variables using ${VAR} syntax."""
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.ENGRAM_DIR", tmp_path / "Engrams"
    )

    create_engram(
        "git_commit", "Commits code", ["git add .", 'git commit -m "${message}"']
    )

    executed_commands = []

    def mock_execute(cmd, d):
        executed_commands.append(cmd)
        return ExecutionResult(success=True, output=f"Ran {cmd}", block_reason="")

    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.cerebellum.execute_command", mock_execute
    )

    # Fire parametric engram
    execute_engram("git_commit", "Studio", params={"message": "Fixed the core loop"})

    assert executed_commands[0] == "git add ."
    assert executed_commands[1] == 'git commit -m "Fixed the core loop"'
