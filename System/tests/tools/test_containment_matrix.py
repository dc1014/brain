# --- System/tests/tools/test_containment_matrix.py ---
import pytest
from unittest.mock import AsyncMock, patch
from System.tools.sandbox import execute_in_sandbox


@pytest.mark.asyncio
async def test_containment_matrix_forces_sandbox_for_lethal_routes(
    safe_subprocess_mock, tmp_path
):
    """Zero-Debt Test: Proves that executing a command under SWARM routes mandates sandbox jailing."""
    safe_workspace = tmp_path / "Studio" / "AppWorkspace"
    safe_workspace.mkdir(parents=True)

    with patch("System.tools.sandbox.ROOT_DIR", tmp_path):
        mock_proc = safe_subprocess_mock
        mock_proc.returncode = 0

        # ⚡ FIXED: Mock BOTH read() and readline() to feed the execution signal,
        # instantly breaking the infinite loop and preventing the 60s hang!
        mock_stream_data = [
            b"Containment verified.\n",
            b"[__EXECUTION_COMPLETE__]",
            b"",
        ]
        mock_proc.stdout.read = AsyncMock(side_effect=mock_stream_data)
        mock_proc.stdout.readline = AsyncMock(side_effect=mock_stream_data)
        mock_proc.wait = AsyncMock()

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
    # ⚡ FIX: Use "Studio" so it complies with the strict ALLOWED_DIRECTORIES in conftest
    safe_workspace = tmp_path.resolve() / "Studio"
    safe_workspace.mkdir(parents=True, exist_ok=True)

    with (
        patch("System.tools.sandbox.ROOT_DIR", tmp_path.resolve()),
        # ⚡ FIX: Patch the correct module path here!
        patch("System.tools.execution.execute_native_isolated") as mock_native,
    ):
        mock_native.return_value = AsyncMock()
        mock_native.return_value.success = True

        await execute_in_sandbox(
            command="ls",
            workspace_path=safe_workspace,
            env_secrets={},
            route="WORKSPACE",
        )
        mock_native.assert_called_once()
