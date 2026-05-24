import json
import os
import asyncio
import hashlib
from rich.console import Console
from System.core.paths import ROOT_DIR, normalize_path
from System.core.locks import StateLock

console = Console()

MD_QUEUE = normalize_path(ROOT_DIR / "Meta" / "Pending_Actions.md")
JSONL_QUEUE = normalize_path(ROOT_DIR / "Meta" / "queue.jsonl")
QUEUE_LOCK = StateLock(normalize_path(ROOT_DIR / "Meta" / "hitl_queue"))


async def apply_motor_inhibition(
    description: str, route_type: str, domain: str
) -> bool:
    """
    Motor Inhibition: Pauses execution of a destructive thought.
    Writes the plan to Obsidian and polls until the human consciously releases the inhibition.
    """
    MD_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    JSONL_QUEUE.parent.mkdir(parents=True, exist_ok=True)

    desc_lower = description.lower()
    if any(x in desc_lower for x in ["rm ", "delete", "drop", "uninstall"]):
        threat_level = "🔴 HIGH (Destructive Data Operation)"
    elif any(x in desc_lower for x in ["install", "pip ", "npm ", "wget", "curl"]):
        threat_level = "🟡 MEDIUM (Network/System Modification)"
    else:
        threat_level = "🟢 LOW (Standard Execution)"

    task_hash = hashlib.md5(description.encode()).hexdigest()[:8]
    release_flag = normalize_path(ROOT_DIR / "Meta" / f".release_{task_hash}")

    payload = {
        "id": task_hash,
        "prompt": description,
        "route_type": route_type,
        "domain": domain,
    }

    with QUEUE_LOCK.acquire_sync():
        with open(JSONL_QUEUE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

        markdown_block = f"""
### 🛑 PENDING ACTION: {route_type} ({domain})
**Threat Level:** {threat_level}
**ID:** `{task_hash}`
**Task:** {description}
*Awaiting human authorization. Press your ShellCommand hotkey to execute.*
---
"""
        with open(MD_QUEUE, "a", encoding="utf-8") as f:
            f.write(markdown_block)

    console.print(
        f"\n[bold magenta]⏸️ Motor Inhibition:[/bold magenta] Task paused. Awaiting human authorization in Obsidian -> [dim]{MD_QUEUE.relative_to(ROOT_DIR)}[/dim]"
    )

    # The Swarm sleeps here. All memory and context is perfectly preserved!
    while True:
        if release_flag.exists():
            try:
                os.remove(release_flag)
            except OSError:
                pass
            console.print(
                f"[bold green]🔓 Inhibition Released:[/bold green] Human authorized task {task_hash}."
            )
            return True

        abort_flag = normalize_path(ROOT_DIR / "System" / ".vagus_abort_signal")
        if abort_flag.exists():
            console.print(
                f"[bold red]🛑 Vagus Nerve activated. Aborting pending task {task_hash}.[/bold red]"
            )
            return False

        await asyncio.sleep(1.0)


def release_motor_inhibition() -> int:
    """Dopaminergic Release: Drops approval flags for all pending tasks."""
    if not JSONL_QUEUE.exists():
        return 0

    approved_count = 0
    with QUEUE_LOCK.acquire_sync():
        with open(JSONL_QUEUE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    desc = data.get("prompt")
                    if desc:
                        # Drop the neurotransmitter flag!
                        task_hash = hashlib.md5(desc.encode()).hexdigest()[:8]
                        normalize_path(
                            ROOT_DIR / "Meta" / f".release_{task_hash}"
                        ).touch()
                        approved_count += 1
                except json.JSONDecodeError:
                    continue

        # We DO NOT delete the queue file here anymore!
        # We leave it for the Medulla daemon to consume.
        if MD_QUEUE.exists():
            with open(MD_QUEUE, "w", encoding="utf-8") as f:
                f.write(
                    "# 🟢 Swarm Action Approved\n*The task has been approved. The Medulla daemon will begin background execution shortly.*\n\n"
                )

    return approved_count
