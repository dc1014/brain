import os
import hmac
import hashlib
import json
import time
import yaml  # type: ignore
import logging
import uvicorn
from logging.handlers import RotatingFileHandler
from collections import defaultdict, deque
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, HTTPException, status
from rich.console import Console

from System.core.paths import ROOT_DIR
from System.neuroanatomy.pathways.spine import transduce_to_spine

console = Console()

# --- DURABLE OBSERVABILITY ---
LOG_DIR = ROOT_DIR / "Sense" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

dermis_logger = logging.getLogger("Dermis")
dermis_logger.setLevel(logging.INFO)
if not dermis_logger.handlers:
    file_handler = RotatingFileHandler(
        LOG_DIR / "dermis.log", maxBytes=5 * 1024 * 1024, backupCount=2
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    dermis_logger.addHandler(file_handler)

# --- HARDENED MEMORY STRUCTURES ---
# Fixed replay window: tracks order of signatures explicitly
RECENT_SIGNATURES_SET: set[str] = set()
RECENT_SIGNATURES_QUEUE: deque[str] = deque()
MAX_SIGNATURE_CACHE = 1000

IP_REQUEST_HISTORY: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0
MAX_REQUESTS_PER_WINDOW = 50
MAX_PAYLOAD_SIZE = 2 * 1024 * 1024  # Strict 2MB ceiling to immunize against OOM bounds

app = FastAPI(title="Brain OS Ingress Receptor", version="2.0.0")
CONFIG_ROUTES: Dict[str, Any] = {}


def load_config_routes():
    global CONFIG_ROUTES
    config_path = ROOT_DIR / "System" / "config" / "webhooks.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            CONFIG_ROUTES = data.get("webhooks", {})


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


def enforce_allostatic_load(client_ip: str) -> bool:
    current_time = time.time()
    # Clean stale request markers
    IP_REQUEST_HISTORY[client_ip] = [
        t for t in IP_REQUEST_HISTORY[client_ip] if current_time - t < RATE_LIMIT_WINDOW
    ]
    if len(IP_REQUEST_HISTORY[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        return False
    IP_REQUEST_HISTORY[client_ip].append(current_time)
    return True


def extract_true_client_ip(request: Request) -> str:
    """Extracts the true client IP from reverse tunnel headers safely."""
    # Read common reverse tunnel forwarding headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Split by comma and strip whitespace to isolate the first originating client address
        addresses = [addr.strip() for addr in forwarded_for.split(",")]
        if addresses:
            return addresses[0]

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "127.0.0.1"


@app.post("/{route_name}")
async def handle_webhook(route_name: str, request: Request):
    client_ip = extract_true_client_ip(request)

    # 1. Evaluate Allostatic Load (Rate Limiting)
    if not enforce_allostatic_load(client_ip):
        msg = f"Rate limit exceeded for IP {client_ip}. Dropping impulse."
        console.print(f"[bold red]🚫 Dermis: {msg}[/bold red]")
        dermis_logger.warning(msg)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded."
        )

    # 2. Match Active Gateway Config Layout
    if route_name not in CONFIG_ROUTES:
        dermis_logger.warning(
            f"404 Not Found: Unknown route '{route_name}' from {client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint unmapped."
        )

    route_info = CONFIG_ROUTES[route_name]

    # 3. Secure Payload Stream Isolation (Anti-OOM Gate)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_PAYLOAD_SIZE:
        dermis_logger.error(
            f"Payload boundary block: {int(content_length)} bytes from {client_ip}"
        )
        raise HTTPException(
            status_code=413,
            detail="Payload exceeds safe limits.",
        )

    # Chunk read bytes safely to prevent large body parsing locks
    raw_body = b""
    async for chunk in request.stream():
        raw_body += chunk
        if len(raw_body) > MAX_PAYLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Payload ceiling breached during stream translation.",
            )

    # 4. Cryptographic Validation Chain
    signature_header = route_info.get("signature_header", "")
    incoming_signature = request.headers.get(signature_header, "")
    secret_key = os.environ.get(route_info.get("secret_env_var", ""), "")

    if not verify_signature(raw_body, secret_key, incoming_signature):
        msg = f"Security block. Invalid signature from {client_ip} on '{route_name}'."
        console.print(f"[bold red]🛡️ Dermis: {msg}[/bold red]")
        dermis_logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature authentication failed.",
        )

    # 5. Deterministic Sliding Replay Mitigation
    if incoming_signature in RECENT_SIGNATURES_SET:
        msg = f"Replay attack detected on '{route_name}'. Dropping duplicate."
        console.print(f"[bold red]♻️ Dermis: {msg}[/bold red]")
        dermis_logger.warning(msg)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate message frame dropped.",
        )

    RECENT_SIGNATURES_SET.add(incoming_signature)
    RECENT_SIGNATURES_QUEUE.append(incoming_signature)

    # Exact sliding FIFO eviction pattern instead of arbitrary popping
    if len(RECENT_SIGNATURES_SET) > MAX_SIGNATURE_CACHE:
        oldest = RECENT_SIGNATURES_QUEUE.popleft()
        RECENT_SIGNATURES_SET.remove(oldest)

    # 6. JSON Transformation & Spine Transduction
    try:
        payload_data = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        dermis_logger.error(f"Malformed JSON received on '{route_name}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed payload structure.",
        )

    mapping = route_info.get("payload_mapping", {})
    extracted_values = {k: _extract_field(payload_data, v) for k, v in mapping.items()}

    template = route_info.get("template", "{body}")
    try:
        final_intent = template.format(**extracted_values)
    except KeyError:
        final_intent = str(extracted_values)

    final_intent = f"<external_stimulus>\n{final_intent}\n</external_stimulus>"

    target_action = route_info.get("target_action", "exteroceptive").lower()

    success_msg = (
        f"Verified webhook '{route_name}' from {client_ip}. Passing to Spine..."
    )
    console.print(f"[dim green]🌐 Dermis: {success_msg}[/dim green]")
    dermis_logger.info(f"TRANSDUCED [{route_name}]: {final_intent}")

    transduce_to_spine(f"webhook:{route_name}", final_intent, target_action)
    return {"status": "transduced"}


class DermisAbstraction:
    """Hardened ASGI Lifecycle Manager ensuring synchronous thread blocking."""

    def __init__(self, port: int = 8080):
        self.port = port
        # ⚡ THE TYPING FIX: Explicitly type hit as an Optional Server instance to appease mypy
        self.server: Optional[uvicorn.Server] = None

    def start(self) -> None:
        """Starts the FastAPI Webhook Ingress server.

        Note: This method executes synchronously and blocks the calling thread,
        allowing the Medulla's supervisor loop to accurately track its health.
        """
        import uvicorn

        load_config_routes()

        if not CONFIG_ROUTES:
            console.print(
                "[dim yellow]Dermis: No active webhooks mapped. Subsystem sleeping.[/dim yellow]"
            )
            return

        config = uvicorn.Config(
            app, host="127.0.0.1", port=self.port, log_level="warning"
        )

        # Instantiate server context safely
        server_instance = uvicorn.Server(config)
        self.server = server_instance

        start_msg = (
            f"Dermis active. Production FastAPI shell listening on port {self.port}..."
        )
        console.print(f"[bold cyan]🛡️ {start_msg}[/bold cyan]")
        dermis_logger.info(start_msg)

        # ⚡ THE VALUE PASSTHROUGH: Call run directly on the verified local reference
        server_instance.run()

    def shutdown(self) -> None:
        """⚡ COOPERATIVE DISENGAGEMENT: Gracefully unwinds active web socket frameworks."""
        if self.server and self.server.started:
            console.print(
                "[dim yellow]🛡️ Dermis Ingress: Received shutdown token. Closing socket channels...[/dim yellow]"
            )
            dermis_logger.info("Cooperative disengagement initiated.")
            self.server.should_exit = True
