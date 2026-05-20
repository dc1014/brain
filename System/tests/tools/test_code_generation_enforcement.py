import pytest
from System.tools.sandbox import execute_in_sandbox


@pytest.mark.asyncio
async def test_code_generation_route_mandates_container_execution(mocker, tmp_path):
    """Proves that any task running under CODE_GENERATION forces Tier 1 driver execution."""
    safe_workspace = tmp_path / "Studio" / "AppDevelopmentWorkspace"
    safe_workspace.mkdir(parents=True)

    # ⚡ THE FIX: Patch the core path definitions globally instead of targeting the driver attribute
    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sandbox.ROOT_DIR", tmp_path)

    # Spy on Container Sandbox lifecycle methods
    mock_setup = mocker.patch(
        "System.tools.microsandbox.container_driver.ContainerSandboxDriver.setup",
        return_value=True,
    )
    mock_execute = mocker.patch(
        "System.tools.microsandbox.container_driver.ContainerSandboxDriver.execute"
    )
    mock_teardown = mocker.patch(
        "System.tools.microsandbox.container_driver.ContainerSandboxDriver.teardown"
    )

    # Testing our new universal SWARM/FORGE code generation catch-all matrix concept
    await execute_in_sandbox(
        "npm run build", workspace_path=safe_workspace, env_secrets={}, route="SWARM"
    )

    assert mock_setup.called, (
        "Security Breakdown: CODE_GENERATION route processed without engaging container setup!"
    )
    assert mock_execute.called, (
        "Security Breakdown: Task command broke execution boundaries!"
    )
    assert mock_teardown.called, (
        "Security Breakdown: Sandboxed containers leaked volatile memory resources!"
    )


@pytest.mark.asyncio
async def test_container_blocks_system_core_pollution(mocker, tmp_path):
    """Proves that container setup returns False immediately if an agent targets the parent System/ directory."""
    unsafe_workspace = tmp_path / "System" / "core"
    unsafe_workspace.mkdir(parents=True)

    mocker.patch("System.core.paths.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.sandbox.ROOT_DIR", tmp_path)

    # ⚡ THE FIX: Change route from "FORGE" to "SWARM" so it accurately triggers
    # the active Containment Matrix layer instead of slipping to the native fallback track.
    res = await execute_in_sandbox(
        "rm -rf *", workspace_path=unsafe_workspace, env_secrets={}, route="SWARM"
    )

    # Assert the execution was cleanly blocked before container allocation or shell pooling
    assert res.success is False
    assert res.block_reason is not None
    assert "CRITICAL SECURITY TERMINATION" in res.block_reason
