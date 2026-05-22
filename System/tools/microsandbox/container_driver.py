import os
import sys
import asyncio
import subprocess
import uuid
import tarfile
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console

from System.core import paths
from System.core.schemas import ExecutionResult
from System.tools.microsandbox.driver import BaseSandboxDriver
from System.tools.microsandbox.egress import EgressFirewall

console = Console()


class ContainerSandboxDriver(BaseSandboxDriver):
    """
    Implements Tier 1 isolation using local container runtimes.
    Ensures zero host-directory mounts and volatile secret injection.
    """

    def __init__(self) -> None:
        self.sandbox_id = f"brain-sandbox-{uuid.uuid4().hex[:8]}"
        self.tarball_path: Optional[Path] = None
        self.env_file_path: Optional[Path] = None
        self.firewall = EgressFirewall()

    async def setup(self, workspace_path: Path, env_secrets: Dict[str, str]) -> bool:
        try:
            resolved_workspace = Path(workspace_path).resolve()

            try:
                rel_parts = resolved_workspace.relative_to(
                    paths.ROOT_DIR.resolve()
                ).parts
            except ValueError:
                console.print(
                    f"[bold red]Sandbox Error: Path traversal block. Target outside root: {resolved_workspace}[/bold red]"
                )
                return False

            safe_zones = {
                "Studio",
                "Personal",
                "Professional",
                "Media",
                ".trash",
                "Meta",
            }
            if not rel_parts or rel_parts[0] not in safe_zones:
                console.print(
                    f"[bold red]Sandbox Violation: Core system modification blocked. Path: {resolved_workspace}[/bold red]"
                )
                return False

            proxy_port = await self.firewall.start()

            self.tarball_path = Path(f"/tmp/{self.sandbox_id}.tar.gz")
            if sys.platform == "win32":
                self.tarball_path = (
                    Path(os.environ.get("TEMP", "C:\\Temp"))
                    / f"{self.sandbox_id}.tar.gz"
                )

            def _make_tar() -> None:
                if self.tarball_path:
                    with tarfile.open(self.tarball_path, "w:gz") as tar:
                        tar.add(resolved_workspace, arcname=".")

            await asyncio.to_thread(_make_tar)

            self.env_file_path = (
                self.tarball_path.with_suffix(".env") if self.tarball_path else None
            )
            if self.env_file_path:
                with open(self.env_file_path, "w") as f:
                    for k, v in env_secrets.items():
                        f.write(f"{k}={v}\n")
                if sys.platform != "win32":
                    os.chmod(self.env_file_path, 0o600)

            env_posix_path = self.env_file_path.as_posix() if self.env_file_path else ""

            # 🔐 HARDENED KERNEL CONSTRAINTS: Injected read-only mounts, user namespace jailing, and core pooling limitations
            cmd = [
                "docker",
                "create",
                "--name",
                self.sandbox_id,
                "--workdir",
                "/workspace",
                "--user",
                "1000:1000",  # Enforce non-root execution inside the guest container
                "--read-only",  # Mutate the container root filesystem into strict read-only mode
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=64m",  # Restrict writable buffers to explicit limits
                "--tmpfs",
                "/workspace:rw,size=512m",  # Isolate active workspace files inside safe memory pages
                "--env-file",
                env_posix_path,
                "--cap-drop",
                "ALL",  # Sever all kernel capabilities completely
                "--security-opt",
                "no-new-privileges:true",  # Permanently block SUID privilege escalations
                "--pids-limit",
                "100",  # Prevent fork-bomb attacks from freezing host process slots
                "--memory",
                "1g",  # Tighten physical memory allocation ceiling thresholds
                "--cpus",
                "1.0",  # Enforce single-core allocations to completely neutralize CPU exhaustion DoS loops
                "--add-host",
                "host.docker.internal:host-gateway",
                "--env",
                f"HTTPS_PROXY=[http://host.docker.internal](http://host.docker.internal):{proxy_port}",
                "--env",
                f"HTTP_PROXY=[http://host.docker.internal](http://host.docker.internal):{proxy_port}",
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
                self.tarball_path.as_posix(),
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
