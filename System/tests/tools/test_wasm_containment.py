# --- System/tests/tools/test_wasm_containment.py ---
import pytest
import shutil
from pathlib import Path
from System.tools.sandbox import execute_in_sandbox


@pytest.mark.asyncio
async def test_python_wasm_environment_is_isolated_from_host(tmp_path: Path) -> None:
    """
    ZERO DEBT PROOF: Proves that Python code executed by the sandbox runs inside
    Pyodide/WASM and cannot access the host operating system's filesystem natively.
    """
    if not shutil.which("deno"):
        pytest.skip("Deno is required to run the WebAssembly isolation tests.")

    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True)

    malicious_script = workspace / "attack.py"

    # This script attempts to read the root directory of the machine.
    # In native Python, this would list host files. In WASM, it sees the virtual Emscripten filesystem.
    malicious_script.write_text(
        "import os\n"
        "print('VIRTUAL_ROOT:', os.listdir('/'))\n"
        "try:\n"
        "    import subprocess\n"
        "    subprocess.run('echo HACKED', shell=True)\n"
        "except Exception as e:\n"
        "    print('BLOCKED:', type(e).__name__)\n",
        encoding="utf-8",
    )

    res = await execute_in_sandbox(
        command="python attack.py",
        workspace_path=workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )

    assert res.success is True
    # 1. Prove we are in the emscripten virtual filesystem (home, tmp, dev), NOT the host Windows/Mac root
    assert "VIRTUAL_ROOT:" in res.output
    assert "dev" in res.output
    assert "home" in res.output

    # 2. Prove subprocess usage is entirely blocked by the WASM architecture
    assert (
        "BLOCKED: NotImplementedError" in res.output or "BLOCKED: OSError" in res.output
    )


@pytest.mark.asyncio
async def test_sandbox_fails_closed_without_deno(tmp_path: Path, monkeypatch) -> None:
    """Proves the system refuses to run untrusted code if the Deno sandbox is missing."""
    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True)

    # Force shutil.which to pretend Deno isn't installed
    monkeypatch.setattr("shutil.which", lambda x: None)

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
