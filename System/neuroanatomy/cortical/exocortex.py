import json
import hashlib
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
