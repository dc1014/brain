import os
import sys
import pytest
import asyncio
from pathlib import Path
from System.tools.execution import (
    execute_command,
    analyze_safe_syntax,
    execute_native_isolated,
)


@pytest.fixture
def bypass_immune_system(mocker, tmp_path):
    """Test Fixture: Bypasses the AST, Amygdala, and Path validation."""
    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(exist_ok=True)
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(studio_dir)),
    )
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.scan_command", return_value=(True, "Safe")
    )
    return studio_dir


@pytest.fixture(autouse=True)
def mock_shutil_which(mocker):
    """Ensures headless environments without full toolchains don't fail the system binary check."""
    import shutil

    original_which = shutil.which

    def side_effect(cmd, *args, **kwargs):
        if cmd in [
            "python",
            "python3",
            "py",
            "uv",
            "npm",
            "npx",
            "pytest",
            "node",
            "echo",
            "bash",
        ]:
            return (
                f"/usr/bin/{cmd}"
                if sys.platform != "win32"
                else f"C:\\Windows\\System32\\{cmd}.exe"
            )
        return original_which(cmd, *args, **kwargs)

    mocker.patch(
        "System.tools.execution.validation.shutil.which", side_effect=side_effect
    )


# -------------------------------------------------------------------------
# CORE EXECUTION PLANE TESTS (TIER 0)
# -------------------------------------------------------------------------


def test_tier_0_hitl_denial(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "0"}
    )
    mocker.patch("System.tools.execution.__init__.asyncio.to_thread", return_value="n")
    result = execute_command(["npm", "run", "build"], "Studio")
    assert result.success is False
    # Updated to match the new, concise security block return text
    assert "User denied execution" in result.output


def test_tier_0_timeout_orphan_pruning(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    mock_process = mocker.AsyncMock()
    mock_process.pid = 9999
    mock_process.stdout = None
    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    def mock_wait_for_side_effect(coro, timeout):
        coro.close()
        raise asyncio.TimeoutError()

    mocker.patch(
        "System.tools.execution.execution_utils.asyncio.wait_for",
        side_effect=mock_wait_for_side_effect,
    )

    if sys.platform == "win32":
        mock_kill = mocker.patch("os.kill")
    else:
        mock_kill = mocker.patch("os.killpg", create=True)
        mocker.patch("os.getpgid", return_value=9999, create=True)

    sleep_script = bypass_immune_system / "sleep.py"
    sleep_script.write_text("import time\ntime.sleep(300)")

    result = execute_command(["python", "sleep.py"], "Studio")

    assert result.success is False
    assert "ERROR: Command timed out" in result.output
    mock_kill.assert_called_once()


def test_env_scrubber_allowlist(mocker):
    from System.tools.execution.execution_utils import get_scrubbed_env

    mocker.patch.dict(
        os.environ,
        {
            "AWS_SECRET_ACCESS_KEY": "hacked_key",
            "STRIPE_API_TOKEN": "stolen_token",
            "PATH": "/usr/bin:/bin",
            "USER": "admin",
        },
    )
    safe_env = get_scrubbed_env()
    assert "PATH" in safe_env
    assert "USER" in safe_env
    assert "AWS_SECRET_ACCESS_KEY" not in safe_env
    assert "STRIPE_API_TOKEN" not in safe_env


@pytest.mark.asyncio
async def test_tier_0_oom_shield(mocker, tmp_path, bypass_immune_system):
    from System.tools.execution.routing import execute_command_async
    from System.tools.execution.execution_utils import MAX_OUTPUT_CHUNKS

    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    mock_process = mocker.AsyncMock()
    mock_process.pid = 9999
    mock_process.returncode = -9

    mock_payloads = [b"SPAM LINE\n"] * (MAX_OUTPUT_CHUNKS + 5) + [b""]
    mock_process.stdout.read = mocker.AsyncMock(side_effect=mock_payloads)

    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    if sys.platform == "win32":
        mock_kill = mocker.patch("os.kill")
    else:
        mock_kill = mocker.patch("os.killpg", create=True)
        mocker.patch("os.getpgid", return_value=9999, create=True)

    mocker.patch(
        "System.neuroanatomy.systemic.microglia.trigger_immune_response_async",
        return_value=(False, "Mocked Microglia Failure"),
    )
    result = await execute_command_async(["echo", "spam"], "Studio")

    assert "SECURITY BLOCK: Execution halted due to excessive output" in result.output
    mock_kill.assert_called_once()


# -------------------------------------------------------------------------
# ZERO-DAY VULNERABILITY PROOFS (PHASES 1-6)
# -------------------------------------------------------------------------


def test_binary_allowlist_blocks_node(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    result = execute_command(["node", "malware.js"], "Studio")
    assert result.success is False
    assert "Execution of 'node' natively is strictly forbidden" in result.output


def test_python_interactive_i_flag_blocked(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    result = execute_command(["python", "-i"], "Studio")
    assert result.success is False
    assert "Python flags (-c, -m, -i) are strictly forbidden" in result.output


def test_defensive_flag_injection_npm(mocker, tmp_path, bypass_immune_system):
    """Zero-Debt: Proves untrusted node lifecycles are automatically neutralized."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    from System.tools.execution.validation import parse_and_validate_args

    args, bins, err = parse_and_validate_args(["npm", "run", "build"])
    assert "--ignore-scripts" in args
    assert err is None


def test_defensive_flag_injection_uv(mocker, tmp_path, bypass_immune_system):
    """Zero-Debt: Proves arbitrary internet package downloads are explicitly blocked."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    from System.tools.execution.validation import parse_and_validate_args

    args, bins, err = parse_and_validate_args(["uv", "run", "pytest"])
    assert "--offline" in args
    assert err is None


def test_nested_sandbox_escape_path_smuggling(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    result_path = execute_command(["npx", "/usr/bin/node", "malware.js"], "Studio")
    assert result_path.success is False
    assert "Smuggled forbidden binary" in result_path.output
    assert "node" in result_path.output


def test_pytest_ast_evasion_blocked(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.scan_python_ast",
        return_value=(False, "AST Violation found"),
    )
    test_file = bypass_immune_system / "test_malware.py"
    test_file.write_text("import os; os.system('bad')")
    result = execute_command(["pytest"], "Studio")
    assert result.success is False
    assert "AST Violation found" in result.output


def test_phantom_extension_ast_bypass_blocked(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.scan_python_ast",
        return_value=(False, "AST Violation found"),
    )
    phantom_script = bypass_immune_system / "data.txt"
    phantom_script.write_text("import os; os.system('bad')")
    result = execute_command(["python", "data.txt"], "Studio")
    assert result.success is False
    assert "AST Violation found" in result.output


def test_pytest_trojan_horse_traversal_blocked(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    result = execute_command(["pytest", "--rootdir=../../../"], "Studio")
    assert result.success is False
    assert (
        "Path traversal and absolute paths are strictly forbidden in pytest arguments"
        in result.output
    )


def test_uv_run_strict_nested_allowlist(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    result = execute_command(
        ["uv", "run", "awk", "BEGIN {system('rm -rf /')}"], "Studio"
    )
    assert result.success is False
    assert (
        "Smuggled nested binary 'awk' is not in the strict allowlist" in result.output
    )


def test_phase5_flag_merging_evasion_blocked(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    result = execute_command(
        ["python", "-Oic", "import os; os.system('rm -rf /')"], "Studio"
    )
    assert result.success is False
    # Adjusted assertion string to validate our pristine Level 1 Lookahead block!
    assert "strictly forbidden" in result.output


def test_phase5_directory_main_payload_blocked(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.scan_python_ast",
        return_value=(False, "AST Violation in __main__"),
    )
    module_dir = bypass_immune_system / "math_utils"
    module_dir.mkdir()
    main_file = module_dir / "__main__.py"
    main_file.write_text("import os; os.system('bad')")
    result = execute_command(["python", "math_utils"], "Studio")
    assert result.success is False
    assert "AST Violation in __main__" in result.output


def test_ast_secondary_payload_smuggling_blocked(
    mocker, tmp_path, bypass_immune_system
):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    safe_script = bypass_immune_system / "safe.py"
    safe_script.write_text("print('I am safe')")
    evil_script = bypass_immune_system / "evil.py"
    evil_script.write_text("import os; os.system('bad')")

    # Inspect the atomic snapshot file content instead of its path name
    def mock_ast_scan(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            if "bad" in f.read():
                return False, "AST Violation in secondary payload"
        return True, "Safe"

    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.scan_python_ast",
        side_effect=mock_ast_scan,
    )
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.wrap_with_apoptosis",
        return_value="wrapped_safe.py",
    )

    result = execute_command(["python", "safe.py", "evil.py"], "Studio")
    assert result.success is False
    assert "AST Violation in secondary payload" in result.output


def test_phase6_pytest_m_flag_allowed(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    mock_process = mocker.AsyncMock()
    mock_process.pid = 9999
    mock_process.returncode = 0
    mock_process.stdout.read = mocker.AsyncMock(side_effect=[b"Tests passed", b""])
    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    result = execute_command(["pytest", "-m", "slow"], "Studio")
    assert result.success is True
    assert "Tests passed" in result.output


# -------------------------------------------------------------------------
# OPTION B DEPLOYMENT & TIER 1 ROUTING TESTS
# -------------------------------------------------------------------------


def test_option_b_tier_0_deployment_blocked(mocker, tmp_path, bypass_immune_system):
    from System.tools.execution import deploy_project

    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret",
        return_value="fake_token",
    )
    result = deploy_project("Studio", provider="custom")
    assert result.success is False
    assert "Deployments mandate Tier 1 (Hardware Sandbox) isolation" in result.output


@pytest.mark.asyncio
async def test_option_b_tier_1_deployment_routed(
    mocker, tmp_path, bypass_immune_system
):
    """Proves deployments route correctly to the hardware sandbox when Tier 1 is active."""
    # Explicitly import the async variant to test cleanly inside the loop
    from System.tools.execution import deploy_project_async
    from System.core.schemas import ExecutionResult

    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "1", "BRAIN_OS_HEADLESS": "1"}
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret",
        return_value="fake_token",
    )

    # Target the sandbox module directly!
    mocker.patch(
        "System.tools.sandbox.execute_in_sandbox",
        return_value=ExecutionResult(
            success=True,
            output="<deployment_success>\nSimulated deploy for Studio\n</deployment_success>",
        ),
    )

    # Await the async function directly to avoid cross-thread loop creation
    result = await deploy_project_async("Studio", provider="custom")
    assert result.success is True
    assert "Simulated deploy" in result.output


# -------------------------------------------------------------------------
# NEW COVERAGE TESTS: AUXILIARY TOOLS & SAD PATHS
# -------------------------------------------------------------------------


def test_execute_command_path_traversal_blocked(mocker, tmp_path):
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(False, "Path Traversal Detected"),
    )
    result = execute_command(["echo", "test"], "Studio")
    assert result.success is False
    assert "Path Traversal Detected" in result.output


def test_execute_command_amygdala_blocked(mocker, tmp_path):
    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, "Studio"),
    )
    mocker.patch(
        "System.neuroanatomy.limbic.amygdala.scan_command",
        return_value=(False, "Semantic Threat Detected"),
    )
    result = execute_command(["echo", "test"], "Studio")
    assert result.success is False
    assert "Semantic Threat Detected" in result.output


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_execute_command_malformed_syntax(
    mocker, tmp_path, bypass_immune_system
):  # ⚡ ADDED HERE
    # Using an unclosed quote to trigger ValueError in shlex
    result = execute_command("echo 'unclosed quote", "Studio")
    assert result.success is False
    assert "Malformed command syntax" in result.output


def test_execute_command_empty(mocker, tmp_path, bypass_immune_system):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    result = execute_command([], "Studio")
    assert result.success is False
    assert "Empty command" in result.output


@pytest.mark.asyncio
async def test_execute_command_immune_healing(mocker, tmp_path, bypass_immune_system):
    from System.tools.execution import execute_command_async

    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    mock_process = mocker.AsyncMock()
    mock_process.pid = 9999
    mock_process.returncode = 1  # Fails!
    mock_process.stdout.read = mocker.AsyncMock(side_effect=[b"error", b""])
    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    # Mock microglia to successfully heal the code
    mocker.patch(
        "System.neuroanatomy.systemic.microglia.trigger_immune_response_async",
        return_value=(True, "Healed successfully!"),
    )

    result = await execute_command_async(["python", "fails.py"], "Studio")
    assert result.success is True
    assert "Healed successfully!" in result.output


def test_analyze_safe_syntax_success(mocker, tmp_path):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.is_safe_path", return_value=True)

    test_file = tmp_path / "valid.py"
    test_file.write_text("print('coverage')")

    mock_run = mocker.patch("System.tools.execution.subprocess.run")
    mock_run.return_value.returncode = 0

    res = analyze_safe_syntax("valid.py")
    assert res.success is True
    assert "Linter passed" in res.output


def test_analyze_safe_syntax_path_traversal(mocker, tmp_path):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.is_safe_path", return_value=False)

    res = analyze_safe_syntax("../outside.py")
    assert res.success is False
    assert "Cannot lint outside allowed directories" in res.output


def test_analyze_safe_syntax_file_not_found(mocker, tmp_path):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.is_safe_path", return_value=True)
    res = analyze_safe_syntax("missing.py")
    assert res.success is False
    assert "does not exist" in res.output


def test_analyze_safe_syntax_unsupported_extension(mocker, tmp_path):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.is_safe_path", return_value=True)
    test_file = tmp_path / "data.txt"
    test_file.write_text("hello")
    res = analyze_safe_syntax("data.txt")
    assert res.success is True
    assert "is not yet implemented" in res.output


def test_analyze_safe_syntax_linter_fails(mocker, tmp_path):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.is_safe_path", return_value=True)
    test_file = tmp_path / "bad.py"
    test_file.write_text("bad syntax")

    mock_run = mocker.patch("System.tools.execution.subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = "error out"
    mock_run.return_value.stderr = "error err"

    res = analyze_safe_syntax("bad.py")
    assert res.success is True
    assert "Linter found errors" in res.output


def test_analyze_safe_syntax_timeout(mocker, tmp_path):
    import subprocess

    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.is_safe_path", return_value=True)
    test_file = tmp_path / "hang.py"
    test_file.write_text("print('hang')")

    mocker.patch(
        "System.tools.execution.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="ruff", timeout=30),
    )
    res = analyze_safe_syntax("hang.py")

    assert res.success is False
    assert "Syntax linter timed out" in res.output


def test_analyze_safe_syntax_exception(mocker, tmp_path):
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.execution.is_safe_path", return_value=True)
    test_file = tmp_path / "crash.py"
    test_file.write_text("print('crash')")

    mocker.patch(
        "System.tools.execution.subprocess.run",
        side_effect=Exception("Unexpected crash"),
    )
    res = analyze_safe_syntax("crash.py")

    assert res.success is False
    assert "Failed to run linter" in res.output


def test_deploy_project_path_traversal(mocker):
    from System.tools.execution import deploy_project

    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(False, "Bad Path"),
    )
    res = deploy_project("../Studio", "custom")
    assert res.success is False
    assert "Cannot deploy from outside sandbox" in res.output


def test_deploy_project_no_token(mocker, tmp_path):
    from System.tools.execution import deploy_project

    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(tmp_path)),
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret", return_value=None
    )
    res = deploy_project("Studio", "custom")
    assert res.success is False
    assert "DEPLOYMENT_TOKEN missing" in res.output


def test_deploy_project_hitl_denial(mocker, tmp_path):
    from System.tools.execution import deploy_project

    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(tmp_path)),
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret",
        return_value="token",
    )
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "1", "BRAIN_OS_HEADLESS": "0"}
    )
    mocker.patch("System.tools.execution.__init__.asyncio.to_thread", return_value="n")
    res = deploy_project("Studio", "custom")
    assert res.success is False
    assert "User explicitly denied deployment" in res.output


def test_sync_wrapper_running_loop(mocker, tmp_path, bypass_immune_system):
    """Proves the synchronous execution wrapper spawns a thread safely if an event loop is already running."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    mock_process = mocker.AsyncMock()
    mock_process.pid = 9999
    mock_process.returncode = 0
    mock_process.stdout.read = mocker.AsyncMock(side_effect=[b"sync success", b""])
    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    async def run_in_loop():
        return execute_command(["echo", "safe"], "Studio")

    result = asyncio.run(run_in_loop())
    assert result.success is True


def test_deploy_sync_wrapper_running_loop(mocker, tmp_path):
    """Proves the synchronous deployment wrapper spawns a thread safely if an event loop is already running."""
    from System.tools.execution import deploy_project

    mocker.patch(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        return_value=(True, str(tmp_path)),
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_secret", return_value=None
    )

    async def run_in_loop():
        return deploy_project("Studio", "custom")

    result = asyncio.run(run_in_loop())
    assert result.success is False
    assert "DEPLOYMENT_TOKEN missing" in result.output


def test_is_port_in_use_check(mocker):
    from System.tools.execution import is_port_in_use

    mock_socket = mocker.patch("System.tools.execution.socket.socket")
    mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 0
    assert is_port_in_use(8080) is True


def test_manage_background_process_routing(mocker):
    from System.tools.execution import manage_background_process

    mock_manage = mocker.patch(
        "System.neuroanatomy.autonomic.proprioception.manage_background_process",
        return_value="Process routed",
    )
    res = manage_background_process("start", command="npm run dev", port=3000)
    assert res == "Process routed"
    mock_manage.assert_called_once()


def test_phase7_flag_parameter_desync_blocked(mocker, tmp_path, bypass_immune_system):
    """Zero-Debt: Proves an agent cannot use parameter-taking flags to desync the AST wrapper using a decoy file."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    decoy_file = bypass_immune_system / "ignore"
    decoy_file.write_text("print('I am a decoy parameter')")

    real_target = bypass_immune_system / "target.py"
    real_target.write_text("print('I am the real execution target')")

    # Align lookahead parser test with the snapshot file payload mechanics
    def mock_ast_scan(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            if "real execution target" in f.read():
                return False, "AST Guard caught real execution target"
        return True, "Safe"

    mocker.patch(
        "System.tools.execution.staging.scan_python_ast",
        side_effect=mock_ast_scan,
    )
    mocker.patch(
        "System.tools.execution.staging.wrap_with_apoptosis",
        return_value="wrapped_target.py",
    )

    result = execute_command(["python", "-W", "ignore", "target.py"], "Studio")

    assert result.success is False
    assert "AST Guard caught real execution target" in result.output


def test_phase8_npx_package_assignment_bypass_blocked(
    mocker, tmp_path, bypass_immune_system
):
    """Zero-Debt: Proves an agent cannot bypass the nested allowlist using npx --package= assignment syntax."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    result = execute_command(["npx", "--package=bash", "forbidden-cmd"], "Studio")

    assert result.success is False
    assert (
        "Smuggled nested binary 'forbidden-cmd' is not in the strict allowlist"
        in result.output
    )


def test_phase9_toctou_atomic_snapshot_enforced(mocker, tmp_path, bypass_immune_system):
    """Zero-Debt: Proves the engine completely mitigates TOCTOU race conditions by executing an isolated snapshot."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    target_script = bypass_immune_system / "race_condition.py"
    target_script.write_text("print('original source')")

    captured_scan_path = None

    def mock_ast_scan(filepath):
        nonlocal captured_scan_path
        captured_scan_path = filepath
        return True, "Safe"

    mocker.patch(
        "System.tools.execution.staging.scan_python_ast",
        side_effect=mock_ast_scan,
    )
    mocker.patch(
        "System.tools.execution.staging.wrap_with_apoptosis",
        return_value="wrapped_snapshot.py",
    )

    mock_exec = mocker.AsyncMock()
    mock_exec.pid = 9999
    mock_exec.returncode = 0
    mock_exec.stdout.read = mocker.AsyncMock(side_effect=[b"success", b""])
    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_exec,
    )

    result = execute_command(["python", "race_condition.py"], "Studio")

    assert result.success is True
    assert captured_scan_path is not None
    # Verify the file scanned was an unpredictable staging copy, completely evading concurrent workspace swaps
    assert "race_condition.py" not in str(captured_scan_path)
    assert ".immutable_snapshot_" in str(captured_scan_path)


def test_phase10_windows_local_binary_hijacking_blocked(
    mocker, tmp_path, bypass_immune_system
):
    """Zero-Debt: Proves an agent cannot hijack execution by dropping a fake binary into the local workspace."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    fake_python = bypass_immune_system / "python.exe"
    fake_python.touch()

    # Patch shutil.which inside the validation sub-module where it's called
    mocker.patch(
        "System.tools.execution.validation.shutil.which", return_value=str(fake_python)
    )

    result = execute_command(["python", "safe_script.py"], "Studio")
    assert result.success is False
    assert "Local binary hijacking detected" in result.output


def test_sensory_compactor_integration(mocker, tmp_path, bypass_immune_system):
    """Zero-Debt: Proves noisy terminal execution blocks get compacted down cleanly."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch.dict(
        os.environ, {"BRAIN_EXECUTION_TIER": "0", "BRAIN_OS_HEADLESS": "1"}
    )

    mock_process = mocker.AsyncMock()
    mock_process.pid = 9999
    mock_process.returncode = 0

    # Simulate a noisy output trace containing ANSI strings and loading spinners
    # Simulate a clean trace block with high-volume logging data
    noisy_stream = (
        b"\x1b[32m[INFO]\x1b[0m Initializing package maps...\n"
        + b"Log frame line item\n" * 100
    )
    mock_process.stdout.read = mocker.AsyncMock(side_effect=[noisy_stream, b""])
    mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec",
        return_value=mock_process,
    )

    result = execute_command(["python", "build.py"], "Studio")
    assert result.success is True
    assert "Initializing" in result.output
    assert "SENSORY COMPACTOR" in result.output


@pytest.mark.asyncio
async def test_execute_native_isolated_bypasses_shell_interpolation(
    mocker, tmp_path: Path
) -> None:
    """Proves that native isolated routes use create_subprocess_exec to prevent shell injection payloads."""
    # We strictly mock create_subprocess_exec to ensure it is the function called
    mock_exec = mocker.patch(
        "System.tools.execution.routing.asyncio.create_subprocess_exec"
    )

    mock_proc = mocker.AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (b"Safe output", b"")
    mock_exec.return_value = mock_proc

    # We simulate an LLM hallucinating a dangerous command separator injection
    malicious_command_list = ["echo", "test", ";", "rm", "-rf", "/"]

    res = await execute_native_isolated(malicious_command_list, tmp_path, {})

    # The test passes ONLY if the arguments were unpacked directly to the executable,
    # meaning the OS will literally try to echo the string "; rm -rf /" rather than executing it.
    mock_exec.assert_called_once_with(
        "echo",
        "test",
        ";",
        "rm",
        "-rf",
        "/",
        cwd=str(tmp_path.resolve()),
        env=mocker.ANY,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    assert res.success
    assert res.output == "Safe output"
