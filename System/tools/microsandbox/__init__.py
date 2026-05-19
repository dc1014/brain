from pathlib import Path
from typing import Dict, Optional
from System.core.schemas import ExecutionResult
from .container_driver import ContainerSandboxDriver


async def run_tier_1_sandbox_async(
    command: str, target_dir: Path, env_secrets: Optional[Dict[str, str]] = None
) -> ExecutionResult:
    """Orchestrates the full Tier 1 Hardware Isolation lifecycle."""
    if env_secrets is None:
        env_secrets = {}

    driver = ContainerSandboxDriver()
    try:
        setup_ok = await driver.setup(target_dir, env_secrets)
        if not setup_ok:
            return ExecutionResult(
                success=False,
                output="SECURITY BLOCK: Sandbox hardware initialization failed.",
                block_reason="Setup Error",
            )

        return await driver.execute(command)
    finally:
        await driver.teardown()
