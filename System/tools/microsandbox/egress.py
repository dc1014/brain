import asyncio
from rich.console import Console

console = Console()

# ⚡ THE STRICT ALLOWLIST: If it's not here, it mathematically cannot be reached.
ALLOWED_DOMAINS = {
    "registry.npmjs.org",
    "api.vercel.com",
    "api.netlify.com",
    "github.com",
    "registry.yarnpkg.com",
    "nodejs.org",
}


class EgressFirewall:
    """Asynchronous HTTP CONNECT proxy that acts as a strict supply-chain firewall."""

    def __init__(self):
        self.server = None
        self.port = 0

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if not line:
                writer.close()
                return

            request_line = line.decode("utf-8", errors="ignore").strip()
            parts = request_line.split(" ")
            if len(parts) < 3:
                writer.close()
                return

            method, url, _ = parts

            # We strictly only support HTTPS (CONNECT) proxying. Raw HTTP is blocked.
            if method == "CONNECT":
                host, port = url.split(":")

                # ⚡ THE FIREWALL GATE
                is_allowed = host in ALLOWED_DOMAINS or any(
                    host.endswith("." + d) for d in ALLOWED_DOMAINS
                )

                if not is_allowed:
                    console.print(
                        f"\n[bold red]🛡️ EGRESS BLOCKED:[/bold red] Sandbox attempted to exfiltrate to forbidden domain: {host}"
                    )
                    writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
                    await writer.drain()
                    writer.close()
                    return

                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()

                try:
                    remote_reader, remote_writer = await asyncio.open_connection(
                        host, port
                    )
                except Exception:
                    writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    await writer.drain()
                    writer.close()
                    return

                async def forward(r: asyncio.StreamReader, w: asyncio.StreamWriter):
                    try:
                        while True:
                            data = await r.read(4096)
                            if not data:
                                break
                            w.write(data)
                            await w.drain()
                    except Exception:
                        pass
                    finally:
                        if not w.is_closing():
                            w.close()

                asyncio.create_task(forward(reader, remote_writer))
                asyncio.create_task(forward(remote_reader, writer))
            else:
                console.print(
                    "\n[bold red]🛡️ EGRESS BLOCKED:[/bold red] Non-TLS (HTTP) traffic is strictly forbidden."
                )
                writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
                await writer.drain()
                writer.close()

        except Exception:
            if not writer.is_closing():
                writer.close()

    async def start(self) -> int:
        """Binds the firewall to all interfaces so the Docker bridge can reach it."""
        self.server = await asyncio.start_server(self.handle_client, "0.0.0.0", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        console.print(f"[dim]🛡️ Egress Firewall armed on port {self.port}[/dim]")
        return self.port

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
