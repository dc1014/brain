import pytest
from System.tools.sandbox import execute_in_sandbox


@pytest.mark.asyncio
async def test_containment_matrix_forces_docker_for_lethal_routes(mocker, tmp_path):
    """
    Zero-Debt Test: Proves that executing a command under SWARM, FORGE, or HERMES
    strictly mandates ContainerSandboxDriver initialization and rejects host breakouts.
    """
    safe_workspace = tmp_path / "Studio" / "AppDevelopmentWorkspace"
    safe_workspace.mkdir(parents=True)

    # 1. Spy on Container Sandbox lifecycle methods
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

    # 2. Fire command explicitly using the lethal SWARM route
    await execute_in_sandbox(
        "npm run build", workspace_path=safe_workspace, env_secrets={}, route="SWARM"
    )

    # 3. Assert absolute enforcement containment parameters
    assert mock_setup.called, (
        "CRITICAL SECURITY REGRESSION: SWARM route processed without engaging container setup!"
    )
    assert mock_execute.called, (
        "CRITICAL SECURITY REGRESSION: Task command broke execution boundaries!"
    )
    assert mock_teardown.called, (
        "CRITICAL SECURITY REGRESSION: Sandboxed containers leaked volatile memory resources!"
    )


@pytest.mark.asyncio
async def test_containment_matrix_allows_native_execution_for_safe_routes(
    mocker, tmp_path
):
    """
    Zero-Debt Test: Proves that safe routes (like WORKSPACE) bypass Docker and hit the native execution wrapper.
    """
    safe_workspace = tmp_path / "Personal"
    safe_workspace.mkdir(parents=True)

    mock_container_setup = mocker.patch(
        "System.tools.microsandbox.container_driver.ContainerSandboxDriver.setup"
    )
    mock_native = mocker.patch("System.tools.execution.execute_native_isolated")

    # Fire command using the safe WORKSPACE route
    await execute_in_sandbox(
        "ls -la", workspace_path=safe_workspace, env_secrets={}, route="WORKSPACE"
    )

    # Assert Docker was bypassed and Native execution was invoked
    assert not mock_container_setup.called, (
        "Performance Bug: Safe WORKSPACE route triggered heavy Docker containerization!"
    )
    assert mock_native.called, (
        "Bug: Native execution fallback failed to trigger for a safe route!"
    )
