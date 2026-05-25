# --- System/tests/tools/test_sandbox_containment.py ---
import os
import pytest
from pathlib import Path
from System.tools.sandbox import execute_in_sandbox


@pytest.fixture
def secure_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@pytest.mark.asyncio
async def test_ffi_lobotomy_escape(secure_workspace: Path, monkeypatch) -> None:
    """DEFCON PROOF: Verifies the Python-to-JS bridge is mathematically blackholed."""
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")

    malicious_script = secure_workspace / "escape.py"
    malicious_script.write_text(
        "import sys\n"
        "print('JS Module:', sys.modules.get('js'))\n"
        "print('Pyodide JS:', sys.modules.get('pyodide_js'))\n"
        "try:\n"
        "    import js\n"
        "except Exception as e:\n"
        "    print('ImportError:', type(e).__name__)\n",
        encoding="utf-8",
    )

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
    """DEFCON PROOF: Verifies the 5MB output stream accumulator violently severs memory flood attacks."""
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")

    malicious_script = secure_workspace / "pipebomb.py"
    malicious_script.write_text(
        "import sys\n"
        "for i in range(10000):\n"
        "    sys.stdout.write('A' * 1024 + '\\n')\n",
        encoding="utf-8",
    )

    mocker.patch("System.tools.sandbox.MAX_BYTES", 50 * 1024)

    result = await execute_in_sandbox(
        f"python {malicious_script.name}",
        workspace_path=secure_workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )

    assert result.success is False
    assert "CRITICAL SECURITY BLOCK: WASM Output Stream Exceeded" in result.output
    assert "Pipe Bomb Prevented" in result.output


@pytest.mark.asyncio
async def test_storage_bomb_guillotine(
    secure_workspace: Path, mocker, monkeypatch
) -> None:
    """DEFCON PROOF: Verifies the asynchronous storage monitor kills disk inflation attacks."""
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")

    malicious_script = secure_workspace / "storage_bomb.py"
    malicious_script.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")

    mocker.patch(
        "System.tools.sandbox._get_directory_size",
        side_effect=[0, 200 * 1024 * 1024],
    )

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
    """DEFCON PROOF: Verifies that the sandbox safely aborts if the Deno runtime is missing from the host."""
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
    assert "CRITICAL SECURITY TERMINATION" in str(result.block_reason)
    assert "Deno runtime is required for secure WebAssembly isolation" in str(
        result.block_reason
    )


@pytest.mark.asyncio
async def test_sandbox_safe_by_default_blocks_execution(mocker, tmp_path: Path) -> None:
    """Proves the system rejects code execution when the global opt-in flag is missing."""
    mocker.patch.dict(os.environ, clear=True)
    mocker.patch("System.tools.sandbox.is_safe_path", return_value=True)

    res = await execute_in_sandbox(
        command="npm install",
        workspace_path=tmp_path,
        env_secrets={},
        route="CODE_GENERATION",
    )

    assert not res.success
    block_reason_str: str = (
        str(res.block_reason) if res.block_reason is not None else ""
    )
    assert "OPT-IN REQUIRED" in block_reason_str


@pytest.mark.asyncio
async def test_sandbox_allows_execution_when_opted_in(mocker, tmp_path: Path) -> None:
    """Proves the system allows WASM containment execution when the user explicitly opts in."""
    mocker.patch.dict(os.environ, {"CORETEX_ENABLE_CODE_EXECUTION": "true"})

    mocker.patch("System.tools.sandbox.is_safe_path", return_value=True)
    mocker.patch("System.tools.sandbox.shutil.which", return_value="/usr/bin/deno")

    mock_proc = mocker.AsyncMock()
    mock_proc.returncode = 0
    mock_proc.stdout.read = mocker.AsyncMock(
        side_effect=[b"Executed cleanly.[__EXECUTION_COMPLETE__]", b""]
    )
    mock_proc.stdin.write = mocker.MagicMock()
    mock_proc.stdin.close = mocker.MagicMock()
    mock_proc.kill = mocker.MagicMock()

    mocker.patch("System.tools.sandbox.get_pre_warmed_worker", return_value=mock_proc)
    mocker.patch("System.tools.sandbox.replenish_worker_pool_detached")

    mock_transducer = mocker.patch(
        "System.neuroanatomy.sensory.somatosensory.SensoryTransducer"
    )
    mock_transducer.return_value.compact_terminal_output.return_value = (
        "Executed cleanly."
    )

    res = await execute_in_sandbox(
        command="npm install",
        workspace_path=tmp_path,
        env_secrets={},
        route="CODE_GENERATION",
    )

    assert res.success
    assert "Executed cleanly" in res.output


@pytest.mark.asyncio
async def test_sandbox_rejects_unmapped_and_unknown_routes_safely(
    mocker, tmp_path: Path
) -> None:
    """Verifies that any route not explicitly whitelisted is failed-closed to safeguard the host system."""
    mocker.patch("System.tools.sandbox.is_safe_path", return_value=True)
    res = await execute_in_sandbox(
        command="echo 'unauthorized action'",
        workspace_path=tmp_path,
        env_secrets={},
        route="ADVERSARIAL_BYPASS_ATTEMPT",
    )
    assert not res.success
    block_reason_str: str = (
        str(res.block_reason) if res.block_reason is not None else ""
    )
    assert "CRITICAL SECURITY BLOCK" in block_reason_str
