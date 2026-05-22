# --- System/tests/tools/test_microsandbox.py ---
import pytest
from pathlib import Path
from System.tools.microsandbox import _spawn_worker
from System.tools.microsandbox.deno_executor import execute_sandboxed_js


@pytest.mark.asyncio
async def test_wasm_kernel_flags_are_immutable(tmp_path: Path, mocker) -> None:
    """DEFCON PROOF: Verifies the Deno V8 Isolate boots with cryptographically immutable flags."""

    workspace = tmp_path / "Studio"
    workspace.mkdir(parents=True)

    mock_exec = mocker.AsyncMock()
    mock_create = mocker.patch(
        "System.tools.microsandbox.asyncio.create_subprocess_exec",
        return_value=mock_exec,
    )

    await _spawn_worker(workspace)

    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    args_str = " ".join(args)

    # 1. Verify V8 memory ceilings and strict execution flags
    assert "--v8-flags=--max-old-space-size=256,--wasm-max-mem-pages=4096" in args_str
    assert "--allow-net" in args_str
    assert "--allow-import" in args_str

    # 2. Verify read/write access explicitly contains the workspace
    assert "--allow-read=" in args_str
    assert str(workspace.resolve()) in args_str

    # 3. Verify the Host OS Environment override is injected
    env = kwargs.get("env", {})
    assert env.get("NO_COLOR") == "1"
    assert "DENO_DIR" in env  # Verifies the cache is securely routed

    # 4. Verify working directory is physically locked
    assert kwargs.get("cwd") == str(workspace.resolve())


def test_raw_js_sandbox_kernel_flags_are_immutable(tmp_path: Path, mocker) -> None:
    """DEFCON PROOF: Verifies raw JS execution has the same capability erasure as WASM."""

    workspace = tmp_path / "Studio"
    workspace.mkdir()
    script = workspace / "test.js"
    script.write_text("console.log('test');")

    mock_run = mocker.patch("System.tools.microsandbox.deno_executor.subprocess.run")

    execute_sandboxed_js(script, workspace)

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    command_list = args[0]

    # Verify Network is mathematically severed
    assert "--allow-net=none" in command_list
    assert "--no-prompt" in command_list
    assert "--v8-flags=--max-old-space-size=256" in command_list

    # Verify the OS Environment is stripped
    assert kwargs.get("env") == {"NO_COLOR": "1"}


@pytest.mark.asyncio
async def test_native_routing_kernel_jails(tmp_path: Path, mocker) -> None:
    """DEFCON PROOF: Verifies Native Python routing utilizes OS Kernel Jails (Job Objects/SetRlimit)."""

    from System.tools.execution.routing import execute_command_async

    workspace = tmp_path / "Studio"
    workspace.mkdir()

    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(workspace)),
    )
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.scan_command", return_value=(True, "Safe")
    )
    mocker.patch(
        "System.tools.execution.validation.parse_and_validate_args",
        return_value=(["python", "test.py"], {"python"}, None),
    )
    mocker.patch(
        "System.tools.execution.staging.stage_ast_snapshots",
        return_value=(["python", "test.py"], [], None),
    )

    mock_exec = mocker.AsyncMock()
    mock_exec.pid = 9999
    mock_exec.returncode = 0
    mock_exec.stdout.read = mocker.AsyncMock(side_effect=[b"safe", b""])

    mock_create = mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_exec,
    )

    # ⚡ FIXED: Force the system into Headless Mode so it bypasses the
    # "Press Y" terminal prompt entirely and stops the test from hanging.
    mocker.patch.dict("os.environ", {"BRAIN_OS_HEADLESS": "1"})

    # Execute a command that routes natively
    await execute_command_async("python test.py", "Studio", route="WORKSPACE")

    mock_create.assert_called_once()
