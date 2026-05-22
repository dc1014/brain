# --- System/tools/sandbox.py ---
import os
from pathlib import Path
from typing import Dict, Set
from rich.console import Console

from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult
from System.tools.microsandbox.container_driver import ContainerSandboxDriver

console = Console()

# --- SHIFT LEFT SECURITY: OS DIRECTORY BOUNDARIES ---

ALLOWED_DIRECTORIES: Set[Path] = {
    normalize_path(ROOT_DIR / "Personal"),
    normalize_path(ROOT_DIR / "Professional"),
    normalize_path(ROOT_DIR / "Studio"),
    normalize_path(ROOT_DIR / "Meta"),
    normalize_path(ROOT_DIR / "Media"),
}

READ_ONLY_DIRECTORIES: Set[Path] = {
    normalize_path(ROOT_DIR / "System"),
}


def _is_windows_junction(path: Path) -> bool:
    """⚡ KERNEL CHECK: Detects NTFS junction points on Windows."""
    if os.name == "nt" and path.is_dir():
        try:
            import ctypes

            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))  # type: ignore[attr-defined]
            return attrs != -1 and bool(attrs & 0x400)
        except Exception:
            pass
    return False


def is_safe_path(target_path: Path | str, require_write: bool = False) -> bool:
    """SHIFT LEFT: Validates if the target path strictly resides within allowed or read-only directories."""
    resolved_target = normalize_path(target_path)

    if resolved_target.exists():
        if resolved_target.is_symlink() or _is_windows_junction(resolved_target):
            return False

    for parent in resolved_target.parents:
        if parent == ROOT_DIR:
            break
        if parent.is_symlink() or _is_windows_junction(parent):
            return False

    for allowed_dir in ALLOWED_DIRECTORIES:
        try:
            resolved_target.relative_to(allowed_dir)
            return True
        except ValueError:
            continue

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

REQUIRES_CONTAINMENT: Set[str] = {
    "SWARM",
    "STATIC_PAGE",
    "CODE_GENERATION",
}

# 🔐 SAFE-BY-DEFAULT WHITELIST: Explicitly authorized native non-coding routes
ALLOWED_NATIVE_ROUTES: Set[str] = {
    "WORKSPACE",
    "DOCUMENTATION",
    "ANALYTICS",
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

    elif route in ALLOWED_NATIVE_ROUTES:
        console.print(
            f"[dim]⚡ Native Execution Authorized (Route: {route}). Bypassing Tier 1 Container.[/dim]"
        )
        from System.tools.execution import execute_native_isolated

        return await execute_native_isolated(command, workspace_path, env_secrets)

    # 🔐 CRITICAL FAIL-CLOSED GATEWAY: Treat all unmapped, arbitrary, or missing routes as hostile and block them instantly
    else:
        console.print(
            f"[bold red]❌ SECURITY BLOCK: Aborting execution track. Route '{route}' is untrusted or unmapped.[/bold red]"
        )
        return ExecutionResult(
            success=False,
            output="",
            block_reason=f"CRITICAL SECURITY BLOCK: Route '{route}' is not explicitly whitelisted for execution.",
        )
