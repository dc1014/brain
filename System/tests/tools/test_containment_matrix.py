# --- System/tests/tools/test_containment_matrix.py ---
import pytest
from unittest.mock import AsyncMock, patch
from System.tools.sandbox import execute_in_sandbox


@pytest.mark.asyncio
async def test_containment_matrix_forces_sandbox_for_lethal_routes(tmp_path):
    """Zero-Debt Test: Proves that executing a command under SWARM routes mandates sandbox jailing."""
    safe_workspace = tmp_path / "Studio" / "AppWorkspace"
    safe_workspace.mkdir(parents=True)

    with patch("System.tools.sandbox.ROOT_DIR", tmp_path):
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"User-space sandbox verified.\n", b"")

        with patch(
            "System.tools.sandbox.get_pre_warmed_worker",
            AsyncMock(return_value=mock_proc),
        ):
            res = await execute_in_sandbox(
                command="node index.js",
                workspace_path=safe_workspace,
                env_secrets={},
                route="SWARM",
            )
            assert res.success is True


@pytest.mark.asyncio
async def test_containment_matrix_allows_native_execution_for_safe_routes(tmp_path):
    """Zero-Debt Test: Proves that safe routes (like WORKSPACE) bypass containment and hit native execution."""
    safe_workspace = tmp_path / "Personal"
    safe_workspace.mkdir(parents=True)

    with (
        patch("System.tools.sandbox.ROOT_DIR", tmp_path),
        patch("System.tools.execution.execute_native_isolated") as mock_native,
    ):
        mock_native.return_value = AsyncMock()

        await execute_in_sandbox(
            command="ls",
            workspace_path=safe_workspace,
            env_secrets={},
            route="WORKSPACE",
        )
        mock_native.assert_called_once()
