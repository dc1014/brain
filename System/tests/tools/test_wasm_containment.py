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


@pytest.mark.asyncio
async def test_os_level_network_guillotine(tmp_path: Path):
    """
    🛡️ ZERO-DEBT TEST: Proves that the Deno --allow-net=none flag physically
    prevents the WebAssembly environment from opening network sockets.
    """
    # ⚡ FIXED: Create an allowed "Studio" directory so the containment matrix allows execution
    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True, exist_ok=True)

    malicious_script = """
import urllib.request
try:
    urllib.request.urlopen("https://google.com", timeout=2)
    print("[FATAL_BREACH] Network was reached!")
except Exception as e:
    print(f"[SECURE] Network blocked at OS level: {e}")
"""

    import os

    os.environ["BRAIN_ENABLE_CODE_EXECUTION"] = "true"

    command = ["-c", malicious_script]

    result = await execute_in_sandbox(
        command=command,
        workspace_path=workspace,  # ⚡ Pass the safe workspace here
        env_secrets={},
        route="CODE_GENERATION",
    )

    # 1. Verify the container did not crash completely
    assert result.success is True, (
        f"Sandbox crashed unexpectedly. Reason: {result.block_reason}"
    )

    # 2. Verify the OS flag successfully blocked the socket
    assert "[FATAL_BREACH]" not in result.output, (
        "CRITICAL: The sandbox reached the internet!"
    )
    assert "[SECURE]" in result.output, (
        "The OS did not block the network call as expected."
    )
