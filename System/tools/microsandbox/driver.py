import abc
from typing import Dict
from pathlib import Path
from System.core.schemas import ExecutionResult


class BaseSandboxDriver(abc.ABC):
    """
    Abstract interface for Tier 1 Hardware Isolation Providers.
    Any engine (Docker, Firecracker, gVisor) must implement this contract.
    """

    @abc.abstractmethod
    async def setup(self, workspace_path: Path, env_secrets: Dict[str, str]) -> bool:
        """Packs the workspace and initializes the sterile guest environment."""
        pass

    @abc.abstractmethod
    async def execute(self, command: str) -> ExecutionResult:
        """Executes the command within the guest and streams telemetry back to the host."""
        pass

    @abc.abstractmethod
    async def teardown(self) -> None:
        """Violently purges the guest VM, memory pages, and ephemeral storage."""
        pass
