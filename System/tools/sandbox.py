import os
from pathlib import Path
from typing import Dict
from rich.console import Console

from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult
from System.tools.microsandbox.container_driver import ContainerSandboxDriver

console = Console()

# --- SHIFT LEFT SECURITY: OS DIRECTORY BOUNDARIES ---

# ⚡ ZERO-DEBT: Myelinate the strict OS boundaries at load time
ALLOWED_DIRECTORIES: set[Path] = {
    normalize_path(ROOT_DIR / "Personal"),
    normalize_path(ROOT_DIR / "Professional"),
    normalize_path(ROOT_DIR / "Studio"),
    normalize_path(ROOT_DIR / "Meta"),
    normalize_path(ROOT_DIR / "Media"),  # The universal binary blob store
}

READ_ONLY_DIRECTORIES: set[Path] = {
    normalize_path(ROOT_DIR / "System"),
}


def _is_windows_junction(path: Path) -> bool:
    """⚡ KERNEL CHECK: Detects NTFS junction points on Windows."""
    if os.name == "nt" and path.is_dir():
        try:
            import ctypes

            # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))  # type: ignore[attr-defined]
            return attrs != -1 and bool(attrs & 0x400)
        except Exception:
            pass
    return False


def is_safe_path(target_path: Path | str, require_write: bool = False) -> bool:
    """
    SHIFT LEFT: Validates if the target path strictly resides within allowed or read-only directories.
    This must be called BEFORE any file system operation is attempted.
    """
    # ⚡ ZERO-DEBT: Force all incoming paths through the Myelin Sheath
    resolved_target = normalize_path(target_path)

    # 1. SHIFT-LEFT: Reject symlinks and Windows junctions directly on the target
    if resolved_target.exists():
        if resolved_target.is_symlink() or _is_windows_junction(resolved_target):
            return False

    # 2. SHIFT-LEFT: Reject symlinks and junctions anywhere in the parent chain
    for parent in resolved_target.parents:
        if parent == ROOT_DIR:
            break
        if parent.is_symlink() or _is_windows_junction(parent):
            return False

    # 3. Check Write-Allowed Zones
    for allowed_dir in ALLOWED_DIRECTORIES:
        try:
            resolved_target.relative_to(allowed_dir)
            return True
        except ValueError:
            continue

    # 4. Check Read-Only Zones (if write is not explicitly required)
    if not require_write:
        for ro_dir in READ_ONLY_DIRECTORIES:
            try:
                resolved_target.relative_to(ro_dir)
                return True
            except ValueError:
                continue

    return False


# =====================================================================
# 🐳 THE CONTAINMENT MATRIX (SHELL EXECUTION ISOLATION)
# =====================================================================

REQUIRES_CONTAINMENT = {
    # "FORGE", later
    "SWARM",
    # "HERMES", later
    "STATIC_PAGE",
    "CODE_GENERATION",
}


async def execute_in_sandbox(
    command: str,
    workspace_path: Path,
    env_secrets: Dict[str, str],
    route: str = "UNKNOWN",
) -> ExecutionResult:
    """
    The Master Execution Router.
    Evaluates the current cognitive pipeline's route and enforces physical security constraints.
    """
    if route in REQUIRES_CONTAINMENT:
        console.print(
            f"[bold cyan]🐳 Containment Matrix Triggered (Route: {route}): Enforcing Tier 1 Ephemeral Sandbox...[/bold cyan]"
        )
        driver = ContainerSandboxDriver()

        is_ready = await driver.setup(workspace_path, env_secrets)
        if not is_ready:
            return ExecutionResult(
                success=False,
                output="",
                block_reason="CRITICAL SECURITY TERMINATION: Docker engine is unreachable or offline.",
            )

        try:
            result = await driver.execute(command)
            return result
        finally:
            await driver.teardown()

    else:
        console.print(
            f"[dim]⚡ Native Execution Authorized (Route: {route}). Bypassing Tier 1 Container.[/dim]"
        )

        from System.tools.execution import execute_native_isolated

        return await execute_native_isolated(command, workspace_path, env_secrets)
