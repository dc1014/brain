# --- System/tests/tools/test_sandbox_containment.py ---
import os
import pytest
import asyncio
from pathlib import Path
from System.tools.sandbox import execute_in_sandbox
from System.core.paths import ROOT_DIR

pytestmark = pytest.mark.skipif(
    not (ROOT_DIR / "System" / "vendor" / "pyodide" / "pyodide.mjs").exists(),
    reason="Pyodide vendor files missing. Run 'ctx setup' first.",
)


@pytest.fixture
def secure_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


class FakeStdin:
    def write(self, data):
        pass

    def close(self):
        pass

    async def drain(self):
        pass

    async def wait_closed(self):
        pass


def create_fake_process(chunks):
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
            self.returncode = None
            self.stdout = FakeStdout()
            self.stdin = FakeStdin()

        def kill(self):
            self.returncode = 1

        async def wait(self):
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

    return FakeProcess()


@pytest.mark.asyncio
async def test_ffi_lobotomy_escape(secure_workspace: Path, monkeypatch, mocker) -> None:
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")
    malicious_script = secure_workspace / "escape.py"
    malicious_script.write_text("import js", encoding="utf-8")

    chunks = [
        b"JS Module: None\n",
        b"Pyodide JS: None\n",
        b"ImportError: ModuleNotFoundError\n",
        b"[__EXECUTION_COMPLETE__]\n",
    ]

    async def mock_worker(*args, **kwargs):
        return create_fake_process(chunks)

    mocker.patch("System.tools.sandbox.get_pre_warmed_worker", side_effect=mock_worker)
    mocker.patch("asyncio.create_subprocess_exec", side_effect=mock_worker)

    result = await execute_in_sandbox(
        f"python {malicious_script.name}",
        workspace_path=secure_workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )
    assert result.success is True
    assert "JS Module: None" in result.output
    assert "Pyodide JS: None" in result.output
    assert "ImportError: ModuleNotFoundError" in result.output


@pytest.mark.asyncio
async def test_pipe_bomb_stream_guillotine(
    secure_workspace: Path, mocker, monkeypatch
) -> None:
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")
    mocker.patch("System.tools.sandbox.MAX_BYTES", 50)

    async def mock_worker(*args, **kwargs):
        proc = create_fake_process([])

        async def infinite_read(*a, **kw):
            return b"A" * 8192

        proc.stdout.read = infinite_read
        return proc

    mocker.patch("System.tools.sandbox.get_pre_warmed_worker", side_effect=mock_worker)
    mocker.patch("asyncio.create_subprocess_exec", side_effect=mock_worker)

    malicious_script = secure_workspace / "pipebomb.py"
    malicious_script.write_text("print('bomb')", encoding="utf-8")

    result = await execute_in_sandbox(
        f"python {malicious_script.name}",
        workspace_path=secure_workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )
    assert result.success is False
    assert "CRITICAL SECURITY BLOCK: WASM Output Stream Exceeded" in result.output


@pytest.mark.asyncio
async def test_storage_bomb_guillotine(
    secure_workspace: Path, mocker, monkeypatch
) -> None:
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")

    # Pad the side_effect heavily so the storage task doesn't hit StopIteration while sleeping
    mocker.patch(
        "System.tools.sandbox._get_directory_size",
        side_effect=[0] + [200 * 1024 * 1024] * 10,
    )

    async def mock_worker(*args, **kwargs):
        proc = create_fake_process([])

        async def slow_read(*a, **kw):
            await asyncio.sleep(2.0)
            return b""

        proc.stdout.read = slow_read
        return proc

    mocker.patch("System.tools.sandbox.get_pre_warmed_worker", side_effect=mock_worker)
    mocker.patch("asyncio.create_subprocess_exec", side_effect=mock_worker)

    malicious_script = secure_workspace / "storage_bomb.py"
    malicious_script.write_text("print('bomb')", encoding="utf-8")

    result = await execute_in_sandbox(
        f"python {malicious_script.name}",
        workspace_path=secure_workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )
    assert result.success is False
    assert "CRITICAL SECURITY BLOCK: Disk Storage Exhaustion Prevented" in result.output


@pytest.mark.asyncio
async def test_missing_deno_runtime_triggers_guillotine(
    secure_workspace: Path, mocker, monkeypatch
) -> None:
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")
    mocker.patch("System.tools.sandbox.shutil.which", return_value=None)

    malicious_script = secure_workspace / "ghost_script.py"
    malicious_script.write_text("print('Hello')", encoding="utf-8")

    result = await execute_in_sandbox(
        f"python {malicious_script.name}",
        workspace_path=secure_workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )
    assert result.success is False
    assert "Deno runtime is required for secure WebAssembly isolation" in str(
        result.block_reason
    )


@pytest.mark.asyncio
async def test_sandbox_safe_by_default_blocks_execution(mocker, tmp_path: Path) -> None:
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch("System.tools.sandbox.is_safe_path", return_value=True)

    res = await execute_in_sandbox(
        command="npm install",
        workspace_path=tmp_path,
        env_secrets={},
        route="CODE_GENERATION",
    )
    assert not res.success
    assert "OPT-IN REQUIRED" in str(res.block_reason)


@pytest.mark.asyncio
async def test_sandbox_allows_execution_when_opted_in(mocker, tmp_path: Path) -> None:
    mocker.patch.dict(os.environ, {"CORETEX_ENABLE_CODE_EXECUTION": "true"})
    mocker.patch("System.tools.sandbox.is_safe_path", return_value=True)
    mocker.patch("System.tools.sandbox.shutil.which", return_value="/usr/bin/deno")

    chunks = [b"Executed cleanly.\n", b"[__EXECUTION_COMPLETE__]\n"]

    async def mock_worker(*args, **kwargs):
        return create_fake_process(chunks)

    mocker.patch("System.tools.sandbox.get_pre_warmed_worker", side_effect=mock_worker)
    mocker.patch("asyncio.create_subprocess_exec", side_effect=mock_worker)
    mocker.patch("System.tools.sandbox.replenish_worker_pool_detached")

    res = await execute_in_sandbox(
        command="npm install",
        workspace_path=tmp_path,
        env_secrets={},
        route="CODE_GENERATION",
    )
    assert res.success is True
    assert "Executed cleanly" in res.output


@pytest.mark.asyncio
async def test_sandbox_rejects_unmapped_and_unknown_routes_safely(
    mocker, tmp_path: Path
) -> None:
    mocker.patch("System.tools.sandbox.is_safe_path", return_value=True)
    res = await execute_in_sandbox(
        command="echo 'unauthorized action'",
        workspace_path=tmp_path,
        env_secrets={},
        route="ADVERSARIAL_BYPASS_ATTEMPT",
    )
    assert not res.success
    assert "CRITICAL SECURITY BLOCK" in str(res.block_reason)
