import asyncio
import json
from typing import Optional
from rich.console import Console
from System.neuroanatomy.pathways.spine import transmit_public_signal

console = Console()


class ExoReceptor:
    """
    The Telepathic Sense Organ.
    Listens for MCP/JSON-RPC packets via a local socket and forwards them to the Spine.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host: str = host
        self.port: int = port
        # ⚡ ZERO-DEBT TYPE ANNOTATION: Declare as an Optional asyncio.Server
        self.server: Optional[asyncio.Server] = None

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Processes incoming raw synaptic pulses from the network."""
        data = await reader.read(8192)  # 🛡️ 8KB Blood-Brain Barrier Hard Limit
        message = data.decode()
        addr = writer.get_extra_info("peername")

        console.print(
            f"[dim cyan]📡 ExoReceptor: Received telepathic pulse from {addr}[/dim cyan]"
        )

        try:
            packet = json.loads(message)
            sender_id = packet.get("sender_id", "")
            payload = packet.get("payload", "")
            signature = packet.get("signature", "")

            # Drop the signal into the Ascending Spinal Tract
            response = transmit_public_signal(sender_id, payload, signature)

            writer.write(response.encode("utf-8"))
            await writer.drain()
        except json.JSONDecodeError:
            writer.write(b"400 Bad Request: Malformed Synaptic Payload")
            await writer.drain()
        except Exception as e:
            writer.write(f"500 Internal Server Error: {str(e)}".encode("utf-8"))
            await writer.drain()

        writer.close()
        await writer.wait_closed()

    async def listen(self) -> None:
        """Starts the continuous sensory loop."""
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        console.print(
            f"[bold green]👂 ExoReceptor active. Listening for external framework pulses on {self.host}:{self.port}...[/bold green]"
        )

        # ⚡ ZERO-DEBT CHECK: Ensure server is explicitly non-None for strict type assertions
        if self.server is not None:
            async with self.server:
                await self.server.serve_forever()
