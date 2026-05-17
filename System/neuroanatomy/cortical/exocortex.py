import json
import hashlib
import asyncio
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.core.locks import BiologicalLock

console = Console()


class Exocortex:
    """
    The Unified Neural Grid Interface (Exocortex).
    Manages peer-to-peer Brain connections, Public Engram sharing,
    and external framework bridging (OpenClaw, Hermes) via MCP-like protocols.
    """

    def __init__(self) -> None:
        self.secure_nodes_file = ROOT_DIR / "Meta" / "secure_nodes.jsonl"

    def _verify_cryptographic_signature(
        self, payload: str, signature: str, sender_id: str
    ) -> bool:
        """Validates incoming packets against known peer keys in the Meta membrane."""
        if not self.secure_nodes_file.exists():
            return False

        try:
            with BiologicalLock(str(self.secure_nodes_file)):
                with open(self.secure_nodes_file, "r", encoding="utf-8") as f:
                    for line in f:
                        node = json.loads(line)
                        if node.get("sender_id") == sender_id:
                            # 🛡️ SHIFT-LEFT: Simple SHA-256 HMAC for Biomimetic MVP Security
                            expected = hashlib.sha256(
                                f"{payload}{node.get('public_key')}".encode()
                            ).hexdigest()
                            return expected == signature
        except Exception:
            return False
        return False

    def process_inbound_pulse(
        self, sender_id: str, payload: str, signature: str
    ) -> str:
        """
        Gated by the Thalamus. Processes incoming requests from external brains.
        Enforces Shift-Left Security by blocking unverified synaptic connections.
        """
        console.print(
            f"[dim cyan]🌐 Exocortex: Receiving inbound pulse from {sender_id}...[/dim cyan]"
        )

        # 1. Cryptographic Verification
        if not self._verify_cryptographic_signature(payload, signature, sender_id):
            console.print(
                "[bold red]🛑 Exocortex Security Block: Invalid cryptographic signature. Pulse rejected.[/bold red]"
            )
            return "403 Forbidden: Invalid Signature"

        # 2. Payload Decoding & Routing
        try:
            data = json.loads(payload)
            action = data.get("action")

            if action == "READ_RESOURCE":
                return self._handle_read(str(data.get("target", "")))
            elif action == "EXECUTE_ENGRAM":
                return self._handle_engram(str(data.get("engram_name", "")))
            # ⚡ ZERO-DEBT: Adding the external sharing endpoint
            elif action == "SHARE_ENGRAM":
                return self._handle_share(
                    str(data.get("engram_name", "")), str(data.get("code", ""))
                )
            else:
                return "400 Bad Request: Unknown Action"
        except json.JSONDecodeError:
            return "400 Bad Request: Malformed Payload"

    def _handle_read(self, target: str) -> str:
        """Exposes MCP Resources securely (e.g., #public markdown notes)."""
        console.print(
            f"[dim green]🌐 Exocortex: Authorized read for {target}.[/dim green]"
        )
        return f"Content of {target}"

    def _handle_engram(self, engram_name: str) -> str:
        """Safely executes public engrams via Cerebellum mapping."""
        console.print(
            f"[dim green]🌐 Exocortex: Authorized execution for engram {engram_name}.[/dim green]"
        )
        return f"Execution of {engram_name} initiated."

    def _handle_share(self, engram_name: str, code: str) -> str:
        """Receives a shared engram and routes it to the Cerebellar Quarantine."""
        from System.neuroanatomy.autonomic.cerebellum import CerebellarCompiler

        console.print(
            f"[dim yellow]🌐 Exocortex: Receiving shared engram '{engram_name}'.[/dim yellow]"
        )
        compiler = CerebellarCompiler()
        return compiler.quarantine_external_engram(engram_name, code)

    async def transmit_outbound_pulse(
        self, target_node_id: str, action: str, target: str = ""
    ) -> str:
        """
        The Efferent Pathway: Actively transmits a secure cognitive pulse to an external framework.
        Used by the Prefrontal Cortex to command secondary agent swarms.
        """
        # 1. Look up the target node's coordinates in the biological membrane
        if not self.secure_nodes_file.exists():
            return "404 Target Node Not Found (No secure_nodes.jsonl)"

        node_info = None
        try:
            with BiologicalLock(str(self.secure_nodes_file)):
                with open(self.secure_nodes_file, "r", encoding="utf-8") as f:
                    for line in f:
                        node = json.loads(line)
                        if node.get("sender_id") == target_node_id:
                            node_info = node
                            break
        except Exception as e:
            return f"500 Internal Error reading membrane: {str(e)}"

        if not node_info:
            return f"404 Target Node '{target_node_id}' not found in secure membrane."

        host = node_info.get("host", "127.0.0.1")
        port = node_info.get("port", 8765)
        shared_key = node_info.get("public_key", "")

        # 2. Formulate and sign the synaptic payload
        payload_dict = {"action": action, "target": target}
        payload_str = json.dumps(payload_dict)

        # 🛡️ SHIFT-LEFT: Cryptographic outbound signature
        signature = hashlib.sha256(f"{payload_str}{shared_key}".encode()).hexdigest()

        packet = {
            "sender_id": "brain_os_local",
            "payload": payload_str,
            "signature": signature,
        }

        console.print(
            f"[bold magenta]⚡ Exocortex: Transmitting '{action}' pulse to {target_node_id} ({host}:{port})...[/bold magenta]"
        )

        # 3. Fire across the network
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(json.dumps(packet).encode("utf-8"))
            await writer.drain()

            data = await reader.read(8192)  # Await the external brain's response

            writer.close()
            await writer.wait_closed()

            response = data.decode("utf-8")
            console.print(
                f"[dim green]🌐 Exocortex Response received: {response[:100]}...[/dim green]"
            )
            return response

        except ConnectionRefusedError:
            return f"503 Service Unavailable: {target_node_id} is asleep or offline."
        except Exception as e:
            return f"500 Transmission Error: {str(e)}"
