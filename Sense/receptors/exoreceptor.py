import json
import time
import asyncio
from typing import Optional, Dict
from rich.console import Console
from aiohttp import web

from System.neuroanatomy.pathways.spine import transmit_public_signal

console = Console()


class SynapticRateLimiter:
    """
    Biomimetic Token Bucket (Synaptic Fatigue).
    Enforces a strict refractory period on incoming network pulses to prevent DDoS flooding.
    """

    def __init__(self, capacity: int = 20, refill_rate: float = 5.0) -> None:
        self.capacity: float = float(capacity)
        self.refill_rate: float = refill_rate
        self.buckets: Dict[str, list[float]] = {}  # IP -> [tokens, last_update]
        self.lock = asyncio.Lock()

    async def acquire(self, client_ip: str) -> bool:
        """Returns True if the pulse can fire, False if experiencing synaptic fatigue."""
        async with self.lock:
            now = time.time()
            if client_ip not in self.buckets:
                self.buckets[client_ip] = [self.capacity - 1.0, now]
                return True

            tokens, last_update = self.buckets[client_ip]

            # Replenish tokens based on elapsed time
            elapsed = now - last_update
            tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

            if tokens >= 1.0:
                self.buckets[client_ip] = [tokens - 1.0, now]
                return True
            else:
                self.buckets[client_ip] = [tokens, now]
                return False


class ExoReceptor:
    """
    The Telepathic Sense Organ (Dual Protocol).
    Listens for ACP (REST) on port 8765 and MCP (TCP) on port 8766 simultaneously.
    Protected by a Biomimetic Rate Limiter.
    """

    def __init__(
        self, host: str = "127.0.0.1", acp_port: int = 8765, mcp_port: int = 8766
    ):
        self.host: str = host
        self.acp_port: int = acp_port
        self.mcp_port: int = mcp_port

        # 🛡️ SHIFT-LEFT: Global Rate Limiting (Allows 20 burst pulses, refills 5 per second)
        self.rate_limiter = SynapticRateLimiter(capacity=20, refill_rate=5.0)

        # 1. Hormonal Stream (ACP / REST)
        self.app = web.Application(client_max_size=8192)
        self.app.router.add_post("/acp/pulse", self.handle_acp_pulse)
        self.runner: Optional[web.AppRunner] = None

        # 2. Electrical Synapse (MCP / TCP)
        self.mcp_server: Optional[asyncio.Server] = None

    async def handle_acp_pulse(self, request: web.Request) -> web.Response:
        """Processes standardized REST agent frameworks."""
        client_ip = request.remote or "unknown"

        # ⚡ ZERO-DEBT: DDoS interception before JSON parsing
        if not await self.rate_limiter.acquire(client_ip):
            console.print(
                f"[bold red]🛑 ExoReceptor (ACP): Synaptic fatigue! Rate limit exceeded for {client_ip}[/bold red]"
            )
            return web.Response(
                text="429 Too Many Requests: Synaptic Fatigue", status=429
            )

        console.print(
            f"[dim cyan]📡 ExoReceptor (ACP): Received REST pulse from {client_ip}[/dim cyan]"
        )
        try:
            data = await request.json()
            response_text = transmit_public_signal(
                data.get("sender_id", ""),
                data.get("payload", ""),
                data.get("signature", ""),
            )

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
        addr = writer.get_extra_info("peername")
        client_ip = addr[0] if addr else "unknown"

        # ⚡ ZERO-DEBT: DDoS interception
        if not await self.rate_limiter.acquire(client_ip):
            console.print(
                f"[bold red]🛑 ExoReceptor (MCP): Synaptic fatigue! Rate limit exceeded for {client_ip}[/bold red]"
            )
            writer.write(b"429 Too Many Requests: Synaptic Fatigue")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        data = await reader.read(8192)
        console.print(
            f"[dim cyan]📡 ExoReceptor (MCP): Received TCP pulse from {client_ip}[/dim cyan]"
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
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.acp_port)
        await site.start()
        console.print(
            f"[bold green]👂 ACP Receptor active. Listening on http://{self.host}:{self.acp_port}/acp/pulse[/bold green]"
        )

        self.mcp_server = await asyncio.start_server(
            self.handle_mcp_client, self.host, self.mcp_port
        )
        console.print(
            f"[bold green]👂 MCP Receptor active. Listening on TCP {self.host}:{self.mcp_port}[/bold green]"
        )

        if self.mcp_server is not None:
            async with self.mcp_server:
                await self.mcp_server.serve_forever()
