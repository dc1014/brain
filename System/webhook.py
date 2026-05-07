"""
Brain OS Webhook — HTTP API surface for Brain.
Exposes POST /task so Auri, ST, or any HTTP client can invoke Brain.

Port: 8002

This is the "address" that makes Brain reachable from outside itself.
Without it, co-opting every ecosystem is vision. With it, it's infrastructure.
"""
import io
import os
import re
import yaml
import httpx
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load Brain's .env before any other imports
load_dotenv(Path(__file__).parent.parent / ".env")
os.environ["BRAIN_OS_HEADLESS"] = "1"

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from rich.console import Console  # noqa: E402

import System.runtime as rt  # noqa: E402
import System.llm as _llm_mod  # noqa: E402
from System.runtime import execute_pipeline  # noqa: E402
from System.llm import get_system_context  # noqa: E402

# Patch the completion binding inside System.llm so execute_pipeline uses stream=False.
# We do this here (after import) so it replaces the module-level name that run_agent resolves.
import litellm as _litellm  # noqa: E402
_orig_completion = _litellm.completion


def _no_stream_completion(*args, **kwargs):
    kwargs["stream"] = False
    return _orig_completion(*args, **kwargs)


_llm_mod.completion = _no_stream_completion  # type: ignore

CONFIG_PATH = Path(__file__).parent / "config" / "agents.yaml"
with open(CONFIG_PATH) as f:
    _AGENT_CONFIG = yaml.safe_load(f)

# Meridian proxy config
_MERIDIAN_BASE = os.getenv("ANTHROPIC_BASE_URL", "http://localhost:3456")
_MERIDIAN_KEY = os.getenv("ANTHROPIC_API_KEY", "sk-sable")
_DISPATCHER_MODEL = "claude-haiku-4-5"


def _dispatch_via_meridian(prompt: str) -> tuple[bool, str, str, str]:
    """
    Run Brain's dispatcher logic using Meridian directly (stream=false).
    Returns (is_valid, reason, route_type, domain).
    Bypasses litellm to avoid SSE parsing issues with the proxy.
    """
    zero = ("NONE", "NONE")

    # Deterministic pre-flight — same rules as runtime.py
    prompt_lower = prompt.lower()
    forbidden_actions = [r"\bdelete\b", r"\bremove\b", r"\berase\b", r"\brm\b"]
    for action in forbidden_actions:
        if re.search(action, prompt_lower):
            word = action.replace(r"\b", "")
            return False, f"Hard Rule: No delete tool. You asked to '{word}'.", *zero

    forbidden_targets = ["system/", ".env", "tools.py", "router.py", "cli.py"]
    for target in forbidden_targets:
        if target in prompt_lower:
            return False, f"Hard Rule: Sandboxed. Cannot target '{target}'.", *zero

    # Call dispatcher via Meridian with stream=false
    dispatcher_cfg = _AGENT_CONFIG["agents"]["dispatcher"]
    system_prompt = dispatcher_cfg["system_prompt"] + get_system_context(["Meta"])

    try:
        resp = httpx.post(
            f"{_MERIDIAN_BASE}/v1/messages",
            headers={
                "x-api-key": _MERIDIAN_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _DISPATCHER_MODEL,
                "max_tokens": 256,
                "stream": False,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract text content (skip thinking blocks)
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                break

        result = text.strip().upper()

        if result.startswith("REJECTED:"):
            return False, result.replace("REJECTED:", "").strip(), *zero

        route = "COMPLEX"
        domain = "NONE"
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("ROUTE:"):
                route = line.split("ROUTE:")[1].strip()
            elif line.startswith("DOMAIN:"):
                domain = line.split("DOMAIN:")[1].strip()

        return True, "Approved.", route, domain

    except Exception as e:
        return False, f"Dispatcher Error: {e}", *zero


app = FastAPI(title="Brain OS Webhook", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class TaskRequest(BaseModel):
    description: str
    obsidian: bool = False


class TaskResponse(BaseModel):
    accepted: bool
    route: str
    domain: str
    reason: str
    output: str


@app.get("/")
def health() -> dict:
    return {"status": "alive", "service": "brain-webhook", "version": "0.1.0"}


@app.post("/task", response_model=TaskResponse)
def run_task(req: TaskRequest) -> TaskResponse:
    """
    Submit a task to Brain OS.
    Dispatcher runs first (shift-left). If obsidian=True, queues for human review.
    Otherwise executes the full agent pipeline and returns captured output.
    """
    is_valid, reason, route_type, domain = _dispatch_via_meridian(req.description)

    if not is_valid:
        return TaskResponse(
            accepted=False, route="NONE", domain="NONE", reason=reason, output=""
        )

    if req.obsidian:
        pending_file = Path(__file__).parent.parent / "System" / "Pending_Actions.md"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        ticket = (
            f"\n### ⏳ Pending Task: {route_type}\n"
            f"**Logged:** {timestamp} | **Domain:** `{domain}`\n"
            f"**Prompt:** {req.description}\n"
            f"- [ ] **Status:** PENDING EXECUTION\n---\n"
        )
        with open(pending_file, "a", encoding="utf-8") as f:
            f.write(ticket)
        return TaskResponse(
            accepted=True,
            route=route_type,
            domain=domain,
            reason="Queued to Obsidian.",
            output="Task staged in System/Pending_Actions.md for human review.",
        )

    buffer = io.StringIO()
    capture_console = Console(file=buffer, highlight=False, no_color=True)
    original_console = rt.console
    rt.console = capture_console

    try:
        execute_pipeline(req.description, route_type, domain)
        output = buffer.getvalue()
        return TaskResponse(
            accepted=True, route=route_type, domain=domain, reason=reason, output=output
        )
    finally:
        rt.console = original_console


if __name__ == "__main__":
    import uvicorn
    print("Brain OS Webhook — http://0.0.0.0:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")
