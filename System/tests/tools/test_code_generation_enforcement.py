# --- System/tests/tools/test_code_generation_enforcement.py ---
import pytest
from unittest.mock import patch
from System.tools.sandbox import execute_in_sandbox


@pytest.mark.asyncio
async def test_code_generation_route_mandates_container_execution(tmp_path):
    """Proves that any task running under CODE_GENERATION forces user-space containment."""
    safe_workspace = tmp_path / "Studio" / "AppDevelopmentWorkspace"
    safe_workspace.mkdir(parents=True)

    with patch("System.tools.sandbox.ROOT_DIR", tmp_path):
        # ⚡ FIXED: Perfectly structure the async/sync bounds to eliminate all Pytest coroutine RuntimeWarnings
        from unittest.mock import Mock, AsyncMock

        mock_stdin = Mock()
        mock_stdin.drain = AsyncMock()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.stdin = mock_stdin
        mock_proc.kill = Mock()

        mock_proc.stdout.read = AsyncMock(
            side_effect=[b"Sandbox verified.\n", b"[__EXECUTION_COMPLETE__]", b""]
        )
        mock_proc.wait = AsyncMock()

        with patch(
            "System.tools.sandbox.get_pre_warmed_worker",
            AsyncMock(return_value=mock_proc),
        ):
            res = await execute_in_sandbox(
                command="python script.py",
                workspace_path=safe_workspace,
                env_secrets={},
                route="CODE_GENERATION",
            )
            assert res.success is True


@pytest.mark.asyncio
async def test_container_blocks_system_core_pollution(tmp_path):
    """Proves that sandbox execution returns a security block immediately if an agent targets restricted directories."""
    unsafe_workspace = tmp_path / "System" / "core"
    unsafe_workspace.mkdir(parents=True)

    with patch("System.tools.sandbox.ROOT_DIR", tmp_path):
        res = await execute_in_sandbox(
            "rm -rf *", workspace_path=unsafe_workspace, env_secrets={}, route="SWARM"
        )

        assert res.success is False
        assert "CRITICAL SECURITY TERMINATION" in res.block_reason
