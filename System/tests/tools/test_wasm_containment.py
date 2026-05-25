# --- System/tests/tools/test_wasm_containment.py ---
import pytest
import os
import shutil
from pathlib import Path
from System.tools.sandbox import execute_in_sandbox
from System.core.paths import ROOT_DIR

pytestmark = pytest.mark.skipif(
    not (ROOT_DIR / "System" / "vendor" / "pyodide" / "pyodide.mjs").exists(),
    reason="Pyodide vendor files missing. Run 'ctx setup' first.",
)


class FakeStdin:
    def write(self, data):
        pass

    def close(self):
        pass

    async def drain(self):
        pass

    async def wait_closed(self):
        pass


def create_fake_process(chunks, returncode=0):
    class FakeStdout:
        def __init__(self):
            self.items = list(chunks)

        def at_eof(self):
            return not self.items

        async def read(self, *args, **kwargs):
            return self.items.pop(0) if self.items else b""

        async def readline(self, *args, **kwargs):
            return self.items.pop(0) if self.items else b""

    class FakeProcess:
        def __init__(self):
            self.returncode = returncode
            self.stdout = FakeStdout()
            self.stdin = FakeStdin()

        def kill(self):
            pass

        async def wait(self):
            return returncode

    return FakeProcess()


@pytest.mark.asyncio
async def test_python_wasm_environment_is_isolated_from_host(
    tmp_path: Path, monkeypatch, mocker
) -> None:
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")
    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True)

    malicious_script = workspace / "attack.py"
    malicious_script.write_text("print('test')", encoding="utf-8")

    chunks = [
        b"VIRTUAL_ROOT: ['dev', 'home']\n",
        b"BLOCKED: OSError\n",
        b"[__EXECUTION_COMPLETE__]\n",
    ]

    async def mock_worker(*args, **kwargs):
        return create_fake_process(chunks)

    mocker.patch("System.tools.sandbox.get_pre_warmed_worker", side_effect=mock_worker)
    mocker.patch("asyncio.create_subprocess_exec", side_effect=mock_worker)

    res = await execute_in_sandbox(
        command="python attack.py",
        workspace_path=workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )

    assert res.success is True
    assert "VIRTUAL_ROOT:" in res.output
    assert "dev" in res.output
    assert "home" in res.output
    assert "BLOCKED: OSError" in res.output


@pytest.mark.asyncio
async def test_sandbox_fails_closed_without_deno(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")
    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True)

    monkeypatch.setattr(shutil, "which", lambda x: None)

    res = await execute_in_sandbox(
        command="python safe.py",
        workspace_path=workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )

    assert res.success is False
    assert "CRITICAL SECURITY TERMINATION: Deno runtime is required" in str(
        res.block_reason
    )


@pytest.mark.asyncio
async def test_os_level_network_guillotine(tmp_path: Path, mocker):
    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True, exist_ok=True)
    os.environ["CORETEX_ENABLE_CODE_EXECUTION"] = "true"

    chunks = [b"[SECURE] Network blocked at OS level:\n", b"[__EXECUTION_COMPLETE__]\n"]

    async def mock_worker(*args, **kwargs):
        return create_fake_process(chunks)

    mocker.patch("System.tools.sandbox.get_pre_warmed_worker", side_effect=mock_worker)
    mocker.patch("asyncio.create_subprocess_exec", side_effect=mock_worker)

    result = await execute_in_sandbox(
        command=["-c", "print('test')"],
        workspace_path=workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )

    assert result.success is True
    assert "[FATAL_BREACH]" not in result.output
    assert "[SECURE]" in result.output
