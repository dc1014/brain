import os
import json
import hmac
import hashlib
import yaml  # type: ignore
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from typing import Any
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.neuroanatomy.pathways.spine import transduce_to_spine

console = Console()

# --- DURABLE OBSERVABILITY (Pain Receptors & Memory) ---
LOG_DIR = ROOT_DIR / "Sense" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

dermis_logger = logging.getLogger("Dermis")
dermis_logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler(
    LOG_DIR / "dermis.log", maxBytes=5 * 1024 * 1024, backupCount=2
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
if not dermis_logger.handlers:
    dermis_logger.addHandler(file_handler)

# --- HARDENING MEMORY STRUCTURES ---
RECENT_SIGNATURES: set[str] = set()
MAX_SIGNATURE_CACHE = 1000

IP_REQUEST_HISTORY: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0
MAX_REQUESTS_PER_WINDOW = 50


def _extract_field(data: dict[str, Any], path: str) -> str:
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return "Unknown"
    return str(current)


def verify_signature(payload: bytes, secret: str, signature: str) -> bool:
    if not secret or not signature:
        return False
    if signature.startswith("sha256="):
        signature = signature[7:]
    computed = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)


class WebhookHandler(BaseHTTPRequestHandler):
    config_routes: dict[str, Any] = {}

    def enforce_allostatic_load(self) -> bool:
        client_ip = self.client_address[0]
        current_time = time.time()

        IP_REQUEST_HISTORY[client_ip] = [
            t
            for t in IP_REQUEST_HISTORY[client_ip]
            if current_time - t < RATE_LIMIT_WINDOW
        ]

        if len(IP_REQUEST_HISTORY[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
            return False

        IP_REQUEST_HISTORY[client_ip].append(current_time)
        return True

    def do_POST(self):
        client_ip = self.client_address[0]
        parsed_path = urlparse(self.path)
        route_name = parsed_path.path.strip("/")

        if not self.enforce_allostatic_load():
            msg = f"Rate limit exceeded for IP {client_ip}. Dropping impulse."
            console.print(f"[bold red]🚫 Dermis: {msg}[/bold red]")
            dermis_logger.warning(msg)
            self.send_response(429)
            self.end_headers()
            return

        if route_name not in self.config_routes:
            dermis_logger.warning(
                f"404 Not Found: Unknown route '{route_name}' from {client_ip}"
            )
            self.send_response(404)
            self.end_headers()
            return

        route_info = self.config_routes[route_name]
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        signature_header = route_info.get("signature_header", "")
        incoming_signature = self.headers.get(signature_header, "")
        secret_key = os.environ.get(route_info.get("secret_env_var", ""), "")

        if not verify_signature(raw_body, secret_key, incoming_signature):
            msg = (
                f"Security block. Invalid signature from {client_ip} on '{route_name}'."
            )
            console.print(f"[bold red]🛡️ Dermis: {msg}[/bold red]")
            dermis_logger.error(msg)
            self.send_response(401)
            self.end_headers()
            return

        if incoming_signature in RECENT_SIGNATURES:
            msg = f"Replay attack detected on '{route_name}'. Dropping duplicate."
            console.print(f"[bold red]♻️ Dermis: {msg}[/bold red]")
            dermis_logger.warning(msg)
            self.send_response(409)
            self.end_headers()
            return

        RECENT_SIGNATURES.add(incoming_signature)
        if len(RECENT_SIGNATURES) > MAX_SIGNATURE_CACHE:
            RECENT_SIGNATURES.pop()

        try:
            payload_data = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            dermis_logger.error(f"Malformed JSON received on '{route_name}'")
            self.send_error(400, "Malformed JSON")
            return

        mapping = route_info.get("payload_mapping", {})
        extracted_values = {
            k: _extract_field(payload_data, v) for k, v in mapping.items()
        }

        template = route_info.get("template", "{body}")
        try:
            final_intent = template.format(**extracted_values)
        except KeyError:
            final_intent = str(extracted_values)

        target_action = route_info.get("target_action", "exteroceptive").lower()

        success_msg = f"Verified webhook '{route_name}'. Passing to Spine..."
        console.print(f"[dim green]🌐 Dermis: {success_msg}[/dim green]")
        dermis_logger.info(f"TRANSDUCED [{route_name}]: {final_intent}")

        transduce_to_spine(f"webhook:{route_name}", final_intent, target_action)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "transduced"}')

    def log_message(self, format, *args):
        status_code = str(args[1])
        if status_code.startswith("2"):
            return
        elif status_code.startswith("4"):
            console.print(
                f"[dim yellow]⚠️ Dermis Warning: {self.client_address[0]} - {args[0]} - {status_code}[/dim yellow]"
            )
        else:
            console.print(
                f"[bold red]❌ Dermis Error: {self.client_address[0]} - {args[0]} - {status_code}[/bold red]"
            )


class ResilientHTTPServer(ThreadingHTTPServer):
    """Overrides default socket bindings to forcefully reclaim the port if it was left hanging."""

    allow_reuse_address = True


class Dermis:
    def __init__(self, port: int = 8080):
        self.port = port
        self.config_path = ROOT_DIR / "System" / "config" / "webhooks.yaml"
        self.server = None

    def start(self):
        if not self.config_path.exists():
            console.print(
                "[dim yellow]Dermis: No webhooks.yaml found. Sleeping.[/dim yellow]"
            )
            return

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)
            WebhookHandler.config_routes = data.get("webhooks", {})

        if not WebhookHandler.config_routes:
            return

        self.server = ResilientHTTPServer(("127.0.0.1", self.port), WebhookHandler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()

        start_msg = f"Dermis active. Threaded skin listening on port {self.port}..."
        console.print(f"[bold cyan]🛡️ {start_msg}[/bold cyan]")
        dermis_logger.info(start_msg)
