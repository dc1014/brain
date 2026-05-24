# --- System/tests/test_sandbox.py ---
import pytest
from unittest.mock import AsyncMock, patch
from System.tools.sandbox import is_safe_path, execute_in_sandbox


def test_is_safe_path_boundaries(tmp_path):
    with patch("System.tools.sandbox.ROOT_DIR", tmp_path):
        studio_dir = tmp_path / "Studio"
        studio_dir.mkdir()

        assert is_safe_path(studio_dir / "app.js") is True
        assert (
            is_safe_path(tmp_path / "System" / "core" / "boot.py", require_write=True)
            is False
        )


@pytest.mark.asyncio
async def test_execute_in_sandbox_requires_containment(tmp_path):
    workspace = tmp_path / "Studio"
    workspace.mkdir()

    # ⚡ FIXED: Completely structure the stdin stream so write/close are synchronous, but drain is async.
    from unittest.mock import Mock, patch

    mock_stdin = Mock()
    mock_stdin.drain = AsyncMock()

    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.stdin = mock_stdin
    mock_proc.kill = Mock()  # Synchronous process assassination

    mock_proc.stdout.read = AsyncMock(
        side_effect=[
            b"User-space sandbox verified.\n",
            b"[__EXECUTION_COMPLETE__]",
            b"",
        ]
    )
    mock_proc.wait = AsyncMock()

    with (
        patch(
            "System.tools.sandbox.get_pre_warmed_worker",
            AsyncMock(return_value=mock_proc),
        ),
        patch("System.tools.sandbox.replenish_worker_pool_detached") as mock_replenish,
    ):
        res = await execute_in_sandbox(
            command="node script.js",
            workspace_path=workspace,
            env_secrets={},
            route="SWARM",
        )

        assert res.success is True
        assert "sandbox verified" in res.output
        mock_replenish.assert_called_once_with(workspace)


@pytest.mark.asyncio
async def test_execute_in_sandbox_security_block(tmp_path):
    safe_workspace = tmp_path.resolve() / "Studio"  # ⚡ Added .resolve() here
    safe_workspace.mkdir(parents=True, exist_ok=True)

    res = await execute_in_sandbox(
        command="malicious_command",
        workspace_path=safe_workspace,
        env_secrets={},
        route="UNMAPPED_HOSTILE_ROUTE",
    )
    assert res.success is False
    assert "CRITICAL SECURITY BLOCK" in str(res.block_reason)
