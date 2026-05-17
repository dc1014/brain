import json
import asyncio
from typing import Optional
from rich.console import Console
from aiohttp import web

from System.neuroanatomy.pathways.spine import transmit_public_signal

console = Console()


class ExoReceptor:
    """
    The Telepathic Sense Organ (Dual Protocol).
    Listens for ACP (REST) on port 8765 and MCP (TCP) on port 8766 simultaneously.
    """

    def __init__(
        self, host: str = "127.0.0.1", acp_port: int = 8765, mcp_port: int = 8766
    ):
        self.host: str = host
        self.acp_port: int = acp_port
        self.mcp_port: int = mcp_port

        # 1. Hormonal Stream (ACP / REST)
        self.app = web.Application(client_max_size=8192)
        self.app.router.add_post("/acp/pulse", self.handle_acp_pulse)
        self.runner: Optional[web.AppRunner] = None

        # 2. Electrical Synapse (MCP / TCP)
        self.mcp_server: Optional[asyncio.Server] = None

    async def handle_acp_pulse(self, request: web.Request) -> web.Response:
        """Processes standardized REST agent frameworks."""
        console.print(
            f"[dim cyan]📡 ExoReceptor (ACP): Received REST pulse from {request.remote}[/dim cyan]"
        )
        try:
            data = await request.json()
            response_text = transmit_public_signal(
                data.get("sender_id", ""),
                data.get("payload", ""),
                data.get("signature", ""),
            )

            # ⚡ ZERO-DEBT: Strict PEP-8 compliant multi-line branching
            if "403" in response_text:
                return web.Response(text=response_text, status=403)
            elif "413" in response_text:
                return web.Response(text=response_text, status=413)
            elif "400" in response_text:
                return web.Response(text=response_text, status=400)

            return web.Response(text=response_text, status=200)

        except json.JSONDecodeError:
            return web.Response(text="400 Bad Request: Malformed JSON", status=400)
        except web.HTTPRequestEntityTooLarge:
            return web.Response(text="413 Payload Too Large: BBB Rejected", status=413)
        except Exception as e:
            return web.Response(text=f"500 Internal Error: {str(e)}", status=500)

    async def handle_mcp_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Processes high-speed raw electrical packets."""
        data = await reader.read(8192)
        addr = writer.get_extra_info("peername")
        console.print(
            f"[dim cyan]📡 ExoReceptor (MCP): Received TCP pulse from {addr}[/dim cyan]"
        )

        try:
            packet = json.loads(data.decode())
            response = transmit_public_signal(
                packet.get("sender_id", ""),
                packet.get("payload", ""),
                packet.get("signature", ""),
            )
            writer.write(response.encode("utf-8"))
            await writer.drain()
        except json.JSONDecodeError:
            writer.write(b"400 Bad Request: Malformed Payload")
            await writer.drain()
        except Exception as e:
            writer.write(f"500 Internal Error: {str(e)}".encode("utf-8"))
            await writer.drain()

        writer.close()
        await writer.wait_closed()

    async def listen(self) -> None:
        """Starts the continuous dual-protocol sensory loops."""
        # Start ACP
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.acp_port)
        await site.start()
        console.print(
            f"[bold green]👂 ACP Receptor active. Listening on http://{self.host}:{self.acp_port}/acp/pulse[/bold green]"
        )

        # Start MCP
        self.mcp_server = await asyncio.start_server(
            self.handle_mcp_client, self.host, self.mcp_port
        )
        console.print(
            f"[bold green]👂 MCP Receptor active. Listening on TCP {self.host}:{self.mcp_port}[/bold green]"
        )

        if self.mcp_server is not None:
            async with self.mcp_server:
                await self.mcp_server.serve_forever()
