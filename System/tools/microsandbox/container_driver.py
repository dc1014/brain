import os
import sys
import uuid
import asyncio
import tarfile
import subprocess
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from System.core.schemas import ExecutionResult
from System.tools.microsandbox.driver import BaseSandboxDriver
from System.tools.microsandbox.egress import EgressFirewall

console = Console()


class ContainerSandboxDriver(BaseSandboxDriver):
    """
    Implements Tier 1 isolation using local container runtimes.
    Ensures zero host-directory mounts and volatile secret injection.
    """

    def __init__(self):
        self.sandbox_id = f"brain-sandbox-{uuid.uuid4().hex[:8]}"
        self.tarball_path: Optional[Path] = None
        self.env_file_path: Optional[Path] = None
        self.firewall = EgressFirewall()

    async def setup(self, workspace_path: Path, env_secrets: Dict[str, str]) -> bool:
        try:
            # PHASE 4: Armed outbound security mesh before container initialization
            proxy_port = await self.firewall.start()

            # PHASE 2: SECURE STAGING
            self.tarball_path = Path(f"/tmp/{self.sandbox_id}.tar.gz")
            if sys.platform == "win32":
                self.tarball_path = (
                    Path(os.environ.get("TEMP", "C:\\Temp"))
                    / f"{self.sandbox_id}.tar.gz"
                )

            def _make_tar():
                with tarfile.open(self.tarball_path, "w:gz") as tar:
                    tar.add(workspace_path, arcname=".")

            await asyncio.to_thread(_make_tar)

            # PHASE 3: VOLATILE TOKEN INOCULATION
            self.env_file_path = self.tarball_path.with_suffix(".env")
            with open(self.env_file_path, "w") as f:
                for k, v in env_secrets.items():
                    f.write(f"{k}={v}\n")
            if sys.platform != "win32":
                os.chmod(self.env_file_path, 0o600)

            # HARDENED KERNEL CONSTRAINTS
            cmd = [
                "docker",
                "create",
                "--name",
                self.sandbox_id,
                "--workdir",
                "/workspace",
                "--env-file",
                str(self.env_file_path),
                "--cap-drop",
                "ALL",  # Amputate capabilities
                "--security-opt",
                "no-new-privileges:true",  # Block SUID privilege escalations
                "--pids-limit",
                "100",  # Limit execution tree threads
                "--memory",
                "1g",  # Set memory ceilings
                "--add-host",
                "host.docker.internal:host-gateway",
                "--env",
                f"HTTPS_PROXY=http://host.docker.internal:{proxy_port}",
                "--env",
                f"HTTP_PROXY=http://host.docker.internal:{proxy_port}",
                "node:20-slim",
                "sh",
                "-c",
                'tar -xzf /tmp/workspace.tar.gz -C /workspace && rm /tmp/workspace.tar.gz && eval "$EXEC_CMD"',
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            await proc.wait()
            if proc.returncode != 0:
                return False

            copy_cmd = [
                "docker",
                "cp",
                str(self.tarball_path),
                f"{self.sandbox_id}:/tmp/workspace.tar.gz",
            ]
            proc_cp = await asyncio.create_subprocess_exec(
                *copy_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            await proc_cp.wait()

            return proc_cp.returncode == 0

        except Exception as e:
            console.print(f"[bold red]Sandbox Setup Error: {str(e)}[/bold red]")
            return False

    async def execute(self, command: str) -> ExecutionResult:
        cmd = ["docker", "start", "-a", self.sandbox_id]
        env = os.environ.copy()
        env["EXEC_CMD"] = command

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        output_chunks = []
        if proc.stdout:
            while True:
                chunk = await proc.stdout.read(4096)
                if not chunk:
                    break
                decoded = chunk.decode(errors="replace")
                console.print(decoded, end="")
                output_chunks.append(decoded)

        await proc.wait()
        full_output = "".join(output_chunks)

        if proc.returncode != 0:
            return ExecutionResult(
                success=False,
                output=full_output,
                block_reason=f"Guest Exit {proc.returncode}",
            )
        return ExecutionResult(success=True, output=full_output)

    async def teardown(self) -> None:
        try:
            await self.firewall.stop()
            if self.tarball_path and self.tarball_path.exists():
                self.tarball_path.unlink()
            if self.env_file_path and self.env_file_path.exists():
                self.env_file_path.unlink()

            cmd = ["docker", "rm", "-f", self.sandbox_id]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            await proc.wait()
        except Exception:
            pass
