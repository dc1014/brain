import pytest
import asyncio
from pathlib import Path
from System.core.schemas import ExecutionResult
from System.tools.microsandbox.container_driver import ContainerSandboxDriver
from System.tools.microsandbox import run_tier_1_sandbox_async


@pytest.fixture
def mock_firewall_lifecycle(mocker):
    """Targeted Fixture: Stub out actual network binding only for container orchestration tests."""
    mocker.patch(
        "System.tools.microsandbox.egress.EgressFirewall.start", return_value=12345
    )
    mocker.patch("System.tools.microsandbox.egress.EgressFirewall.stop")


@pytest.fixture
def mock_subprocess(mocker):
    """Provides a reusable async subprocess mock."""
    mock_proc = mocker.AsyncMock()
    mock_proc.returncode = 0
    mock_proc.stdout.read = mocker.AsyncMock(side_effect=[b"mocked output\n", b""])
    mocker.patch(
        "System.tools.microsandbox.container_driver.asyncio.create_subprocess_exec",
        return_value=mock_proc,
    )
    return mock_proc


# -------------------------------------------------------------------------
# SETUP PHASE TESTS (Firewall Mock Explicitly Injected)
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_success_unix(
    mocker, mock_subprocess, mock_firewall_lifecycle, tmp_path
):
    """Proves the tarball is packed and Docker is correctly initialized on Unix."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.microsandbox.container_driver.sys.platform", "linux")
    mocker.patch("System.tools.microsandbox.container_driver.tarfile.open")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mock_chmod = mocker.patch("System.tools.microsandbox.container_driver.os.chmod")

    # ⚡ THE FIX: Use a safe, validated path so the sandbox doesn't block it
    safe_workspace = tmp_path / "Studio" / "workspace"
    safe_workspace.mkdir(parents=True)

    driver = ContainerSandboxDriver()
    success = await driver.setup(safe_workspace, {"DEPLOYMENT_TOKEN": "secret123"})

    assert success is True
    mock_chmod.assert_called_once_with(driver.env_file_path, 0o600)
    mock_open().write.assert_called_with("DEPLOYMENT_TOKEN=secret123\n")


@pytest.mark.asyncio
async def test_setup_success_win32(
    mocker, mock_subprocess, mock_firewall_lifecycle, tmp_path
):
    """Proves the setup path adapts correctly for Windows OS file constraints."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.microsandbox.container_driver.sys.platform", "win32")
    mocker.patch("System.tools.microsandbox.container_driver.tarfile.open")
    mocker.patch("builtins.open", mocker.mock_open())
    mock_chmod = mocker.patch("System.tools.microsandbox.container_driver.os.chmod")

    safe_workspace = tmp_path / "Studio" / "workspace"
    safe_workspace.mkdir(parents=True)

    driver = ContainerSandboxDriver()
    success = await driver.setup(safe_workspace, {"TOKEN": "123"})

    assert success is True
    mock_chmod.assert_not_called()


@pytest.mark.asyncio
async def test_setup_docker_create_fails(
    mocker, mock_subprocess, mock_firewall_lifecycle, tmp_path
):
    """Proves setup safely aborts if the Docker container fails to create."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    safe_workspace = tmp_path / "Studio" / "workspace"
    safe_workspace.mkdir(parents=True)

    mocker.patch("System.tools.microsandbox.container_driver.tarfile.open")
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("System.tools.microsandbox.container_driver.os.chmod")

    mock_subprocess.returncode = 1

    driver = ContainerSandboxDriver()
    success = await driver.setup(safe_workspace, {})

    assert success is False


@pytest.mark.asyncio
async def test_setup_exception_caught(mocker, mock_firewall_lifecycle, tmp_path):
    """Proves unexpected file system exceptions during setup are caught gracefully."""
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    safe_workspace = tmp_path / "Studio" / "workspace"
    safe_workspace.mkdir(parents=True)

    mocker.patch(
        "System.tools.microsandbox.container_driver.tarfile.open",
        side_effect=Exception("Disk full"),
    )

    driver = ContainerSandboxDriver()
    success = await driver.setup(safe_workspace, {})

    assert success is False


# -------------------------------------------------------------------------
# EXECUTION PHASE TESTS (Firewall Mock Explicitly Injected)
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_success(mocker, mock_subprocess, mock_firewall_lifecycle):
    """Proves the execution layer successfully streams container telemetry."""
    driver = ContainerSandboxDriver()
    driver.sandbox_id = "test-sandbox"

    result = await driver.execute("npm run build")

    assert result.success is True
    assert "mocked output" in result.output


@pytest.mark.asyncio
async def test_execute_failure(mocker, mock_subprocess, mock_firewall_lifecycle):
    """Proves that a failed guest command returns a properly formatted failure state."""
    mock_subprocess.returncode = 127

    driver = ContainerSandboxDriver()
    result = await driver.execute("npm run fail")

    assert result.success is False
    assert result.block_reason == "Guest Exit 127"


# -------------------------------------------------------------------------
# TEARDOWN & CLEANUP TESTS (Firewall Mock Explicitly Injected)
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_cleans_resources(
    mocker, mock_subprocess, mock_firewall_lifecycle
):
    """Proves the zero-residual cleanup purges tarballs, env files, and containers."""
    driver = ContainerSandboxDriver()
    driver.sandbox_id = "test-sandbox"
    driver.tarball_path = mocker.MagicMock(spec=Path)
    driver.tarball_path.exists.return_value = True
    driver.env_file_path = mocker.MagicMock(spec=Path)
    driver.env_file_path.exists.return_value = True

    await driver.teardown()

    driver.tarball_path.unlink.assert_called_once()
    driver.env_file_path.unlink.assert_called_once()


@pytest.mark.asyncio
async def test_teardown_handles_missing_files_and_exceptions(
    mocker, mock_firewall_lifecycle
):
    """Proves teardown will not crash the system if cleanup files are already gone."""
    mocker.patch(
        "System.tools.microsandbox.container_driver.asyncio.create_subprocess_exec",
        side_effect=Exception("Docker socket missing"),
    )

    driver = ContainerSandboxDriver()
    driver.tarball_path = mocker.MagicMock(spec=Path)
    driver.tarball_path.exists.return_value = False
    driver.env_file_path = None

    await driver.teardown()
    driver.tarball_path.unlink.assert_not_called()


# -------------------------------------------------------------------------
# ROUTER / ORCHESTRATOR TESTS
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_router_success(mocker):
    """Proves the router correctly chains setup, execution, and teardown."""
    mock_driver = mocker.MagicMock()
    mock_driver.setup = mocker.AsyncMock(return_value=True)
    mock_driver.execute = mocker.AsyncMock(
        return_value=ExecutionResult(success=True, output="Deploy OK")
    )
    mock_driver.teardown = mocker.AsyncMock()

    mocker.patch(
        "System.tools.microsandbox.ContainerSandboxDriver", return_value=mock_driver
    )

    result = await run_tier_1_sandbox_async("deploy", Path("/Studio"), {"TOKEN": "123"})

    assert result.success is True
    assert result.output == "Deploy OK"
    mock_driver.teardown.assert_called_once()


@pytest.mark.asyncio
async def test_router_setup_failure(mocker):
    """Proves the router aborts and cleans up if setup fails."""
    mock_driver = mocker.MagicMock()
    mock_driver.setup = mocker.AsyncMock(return_value=False)
    mock_driver.execute = mocker.AsyncMock()
    mock_driver.teardown = mocker.AsyncMock()

    mocker.patch(
        "System.tools.microsandbox.ContainerSandboxDriver", return_value=mock_driver
    )

    result = await run_tier_1_sandbox_async("deploy", Path("/Studio"))

    assert result.success is False
    assert "initialization failed" in result.output
    mock_driver.execute.assert_not_called()
    mock_driver.teardown.assert_called_once()


# -------------------------------------------------------------------------
# EGRESS FIREWALL PROOFS (No Mock - Tests Live Code Paths)
# -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_egress_firewall_lifecycle(mocker):
    """Proves the firewall binds successfully and tears down cleanly."""
    from System.tools.microsandbox.egress import EgressFirewall

    firewall = EgressFirewall()

    port = await firewall.start()
    assert port > 0
    assert firewall.server is not None

    await firewall.stop()


@pytest.mark.asyncio
async def test_egress_firewall_blocks_evil_domain(mocker):
    """Proves the firewall strictly drops requests to unapproved supply-chain domains."""
    from System.tools.microsandbox.egress import EgressFirewall

    firewall = EgressFirewall()

    mock_reader = mocker.AsyncMock()
    mock_reader.readline.return_value = b"CONNECT evil-hacker.com:443 HTTP/1.1\r\n"
    mock_writer = mocker.AsyncMock()

    await firewall.handle_client(mock_reader, mock_writer)

    mock_writer.write.assert_called_with(b"HTTP/1.1 403 Forbidden\r\n\r\n")
    mock_writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_egress_firewall_allows_vercel(mocker):
    """Proves the firewall successfully routes traffic to approved domains like Vercel."""
    from System.tools.microsandbox.egress import EgressFirewall

    firewall = EgressFirewall()

    mock_reader = mocker.AsyncMock()
    mock_reader.readline.return_value = b"CONNECT api.vercel.com:443 HTTP/1.1\r\n"
    mock_reader.read.return_value = b""
    mock_writer = mocker.AsyncMock()

    mock_remote_reader = mocker.AsyncMock()
    mock_remote_reader.read.return_value = b""
    mock_remote_writer = mocker.AsyncMock()

    mocker.patch(
        "System.tools.microsandbox.egress.asyncio.open_connection",
        return_value=(mock_remote_reader, mock_remote_writer),
    )

    await firewall.handle_client(mock_reader, mock_writer)
    await asyncio.sleep(0.01)

    mock_writer.write.assert_any_call(b"HTTP/1.1 200 Connection Established\r\n\r\n")


@pytest.mark.asyncio
async def test_egress_firewall_blocks_raw_http(mocker):
    """Proves the firewall blocks unencrypted HTTP traffic to prevent sniffing."""
    from System.tools.microsandbox.egress import EgressFirewall

    firewall = EgressFirewall()

    mock_reader = mocker.AsyncMock()
    mock_reader.readline.return_value = b"GET http://api.vercel.com/ HTTP/1.1\r\n"
    mock_writer = mocker.AsyncMock()

    await firewall.handle_client(mock_reader, mock_writer)

    mock_writer.write.assert_called_with(b"HTTP/1.1 403 Forbidden\r\n\r\n")
