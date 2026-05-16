from System.neuroanatomy.autonomic.cerebellum import (
    create_engram,
    execute_engram,
    list_engrams,
)
from System.core.schemas import ExecutionResult
from System.neuroanatomy.autonomic.cerebellum import CerebellarCompiler


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


def test_cerebellum_compiler_success(mocker, tmp_path, monkeypatch):
    """Proves the Cerebellum can extract Python code and detect Exocortex manifests."""
    # ⚡ ZERO-DEBT: Mock BOTH paths so relative_to() mathematically aligns in the isolated test environment
    monkeypatch.setattr("System.neuroanatomy.autonomic.cerebellum.ENGRAM_DIR", tmp_path)
    monkeypatch.setattr("System.neuroanatomy.autonomic.cerebellum.ROOT_DIR", tmp_path)

    class MockMessage:
        content = (
            "```python\n"
            "EXOCORTEX_MANIFEST = {\n"
            "    'name': 'cleanup_logs',\n"
            "    'description': 'Deletes old logs.'\n"
            "}\n\n"
            "def execute_reflex():\n"
            "    pass\n"
            "```"
        )

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    mocker.patch(
        "System.neuroanatomy.autonomic.cerebellum.completion",
        return_value=MockResponse(),
    )

    compiler = CerebellarCompiler()
    engram_name = compiler.compile_engram("Clean logs", "I ran rm -rf logs")

    assert engram_name == "cleanup_logs"
    assert (tmp_path / "cleanup_logs.py").exists()

    written_code = (tmp_path / "cleanup_logs.py").read_text(encoding="utf-8")
    assert "EXOCORTEX_MANIFEST" in written_code
    assert "def execute_reflex()" in written_code


def test_cerebellum_fallback_name(mocker, tmp_path, monkeypatch):
    """Proves the compiler falls back to a safe name if the LLM forgets the manifest."""
    # ⚡ ZERO-DEBT: Mock BOTH paths so relative_to() mathematically aligns in the isolated test environment
    monkeypatch.setattr("System.neuroanatomy.autonomic.cerebellum.ENGRAM_DIR", tmp_path)
    monkeypatch.setattr("System.neuroanatomy.autonomic.cerebellum.ROOT_DIR", tmp_path)

    class MockMessage:
        content = "print('No manifest here')"

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    mocker.patch(
        "System.neuroanatomy.autonomic.cerebellum.completion",
        return_value=MockResponse(),
    )

    compiler = CerebellarCompiler()
    engram_name = compiler.compile_engram("Do stuff", "Trace")

    assert engram_name == "unnamed_reflex"
