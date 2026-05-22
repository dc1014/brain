# --- System/tests/tools/test_sandbox_containment.py ---
import pytest
from pathlib import Path
from System.tools.sandbox import execute_in_sandbox, is_safe_path


@pytest.mark.asyncio
async def test_sandbox_rejects_unmapped_and_unknown_routes_safely(
    tmp_path: Path,
) -> None:
    """Verifies that any route not explicitly whitelisted is failed-closed to safeguard the host system."""
    res = await execute_in_sandbox(
        command="echo 'unauthorized action'",
        workspace_path=tmp_path,
        env_secrets={},
        route="ADVERSARIAL_BYPASS_ATTEMPT",
    )
    assert not res.success

    block_reason_str: str = (
        str(res.block_reason) if res.block_reason is not None else ""
    )

    # ⚡ ASSERTION REALIGNMENT: Checks for the proper updated shift-left validation error string
    assert "CRITICAL SECURITY TERMINATION" in block_reason_str


def test_is_safe_path_blocks_directory_traversal(tmp_path: Path) -> None:
    """Confirms filesystem path validations correctly intercept out-of-bounds escape sequences."""
    unsafe_target = tmp_path / "../../etc/passwd"
    assert not is_safe_path(unsafe_target, require_write=True)
