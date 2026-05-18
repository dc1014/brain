import json
import asyncio
import sqlite3
import time
import os

from datetime import datetime
from rich.console import Console
from System.core.paths import ROOT_DIR
from System.llm import acompletion
from System.neuroanatomy.systemic.immune_system import vault

console = Console()


DB_PATH = ROOT_DIR / "System" / "config" / "hippocampus.db"

QUEUE_FILE_PATH = ROOT_DIR / "System" / "execution_queue.json"

# =====================================================================
# 1. EPHEMERAL WORKING MEMORY (SQLite FTS5)
# =====================================================================


def _get_conn() -> sqlite3.Connection:
    """Initializes the FTS5 virtual table for blazingly fast full-text search."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories
        USING fts5(filepath, content, timestamp UNINDEXED);
    """)
    return conn


def encode_memory(filepath: str, content: str) -> None:
    """Encodes a file into the ephemeral index. Replaces existing index for the same file."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE filepath = ?", (filepath,))
        cursor.execute(
            "INSERT INTO memories (filepath, content, timestamp) VALUES (?, ?, ?)",
            (filepath, content, int(time.time())),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        console.print(f"[dim red]Hippocampus encoding error: {e}[/dim red]")


def rebuild_index() -> None:
    """Completely wipes and rebuilds the SQLite index from the flat-file Glass Brain."""
    console.print("[dim]🧠 Hippocampus: Rebuilding ephemeral search index...[/dim]")
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except PermissionError:
            console.print(
                "[bold red]🛑 Cannot rebuild index: Database is locked.[/bold red]"
            )
            return

    conn = _get_conn()
    cursor = conn.cursor()

    valid_exts = {".py", ".ts", ".tsx", ".md", ".json", ".txt"}
    ignore_dirs = {
        ".git",
        "node_modules",
        ".venv",
        "__pycache__",
        "dist",
        "build",
        "logs",
    }
    core_domains = ["Studio", "Meta", "Personal", "Professional"]

    for target in core_domains:
        target_dir = ROOT_DIR / target
        if not target_dir.exists():
            continue

        for filepath in target_dir.rglob("*"):
            if filepath.is_file() and filepath.suffix in valid_exts:
                if any(ignored in filepath.parts for ignored in ignore_dirs):
                    continue
                try:
                    content = filepath.read_text(encoding="utf-8")
                    rel_path = str(filepath.relative_to(ROOT_DIR))
                    cursor.execute(
                        "INSERT INTO memories (filepath, content, timestamp) VALUES (?, ?, ?)",
                        (rel_path, content, int(time.time())),
                    )
                except Exception:
                    continue

    conn.commit()
    conn.close()
    console.print(
        "[bold green]✨ Hippocampus index successfully rebuilt from flat files![/bold green]"
    )


def recall_memory(query: str, limit: int = 5) -> str:
    """Searches the index for keywords. Uses exact phrase matching to prevent FTS5 injection attacks."""
    if not DB_PATH.exists():
        rebuild_index()

    try:
        conn = _get_conn()
        cursor = conn.cursor()
        safe_query = '"' + query.replace('"', '""') + '"'

        cursor.execute(
            """
            SELECT filepath, snippet(memories, 1, '[MARK] ', ' [/MARK]', '...', 25)
            FROM memories
            WHERE memories MATCH ?
            ORDER BY rank
            LIMIT ?
        """,
            (safe_query, limit),
        )

        results = cursor.fetchall()
        conn.close()

        if not results:
            return f"No memories found for '{query}'."

        formatted_results = []
        for filepath, snippet in results:
            formatted_results.append(f"--- {filepath} ---\n...{snippet}...\n")

        return "\n".join(formatted_results)

    except Exception as e:
        return f"Hippocampus recall error: {str(e)}"


# =====================================================================
# 2. SYNAPTIC CONSOLIDATION (Long-Term Domain Memory)
# =====================================================================


async def _encode_short_term_memory() -> None:
    """Summarizes active JSONL ledgers into dense, long-term markdown memories by DOMAIN."""
    ledgers = list(ROOT_DIR.rglob("agent_interactions.jsonl"))

    # 🧠 Spatial Routing: Group memories by their Domain context
    domain_events: dict[str, list[str]] = {}

    for ledger in ledgers:
        if ledger.is_file():
            try:
                lines = ledger.read_text(encoding="utf-8").splitlines()
                for line in lines[-50:]:
                    try:
                        data = json.loads(line)
                        agent = data.get("agent", "Unknown")
                        domain = data.get("domain", "META").upper()

                        if domain in ["NONE", "", "UNKNOWN"]:
                            domain = "META"

                        prompt = data.get("user_prompt", "")[:100]
                        response = data.get("response", "")[:200]

                        event_str = f"[{agent}] Task: {prompt} | Result: {response}"

                        if domain not in domain_events:
                            domain_events[domain] = []
                        domain_events[domain].append(event_str)
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass

    if not domain_events:
        console.print(
            "[dim]🧠 Hippocampus: No short-term memories found to consolidate.[/dim]"
        )
        return

    model = (
        "gemini/gemini-2.5-flash"
        if vault.get_api_key_for_model("gemini/")
        else "openai/gpt-4o-mini"
    )
    api_key = vault.get_api_key_for_model(model)

    if not api_key:
        console.print(
            "[dim yellow]⚠️ Hippocampus: No API key found for consolidation model. Skipping encoding.[/dim yellow]"
        )
        return

    for domain, events in domain_events.items():
        console.print(
            f"[blue]🧠 Hippocampus: Consolidating memory for the {domain} domain...[/blue]"
        )

        memory_payload = "\n".join(events)
        prompt = (
            f"You are the Hippocampus of Brain OS. Summarize the following recent agent interactions for the {domain} domain into a brief, "
            "bulleted list of completed tasks, architectural changes, or context. Focus purely on technical facts.\n\n"
            f"RAW LOGS:\n{memory_payload}"
        )

        try:
            response = await acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                api_key=api_key,
            )
            summary = str(response.choices[0].message.content).strip()

            if domain == "META":
                memory_file = ROOT_DIR / "Meta" / "global-memory.md"
                dir_name = "Meta"
                file_name = "global-memory.md"
            else:
                dir_name = domain.capitalize()
                file_name = f"{domain.lower()}-memory.md"
                memory_file = ROOT_DIR / dir_name / file_name

            memory_file.parent.mkdir(parents=True, exist_ok=True)

            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            append_text = f"\n\n### Synaptic Consolidation ({date_str})\n{summary}\n"

            with open(memory_file, "a", encoding="utf-8") as f:
                f.write(append_text)

            console.print(
                f"[bold green]🧠 Hippocampus: Memory successfully encoded to {dir_name}/{file_name}.[/bold green]"
            )
        except Exception as e:
            console.print(
                f"[bold red]⚠️ Hippocampus Error encoding {domain} memory: {e}[/bold red]"
            )


def consolidate_short_term_memory() -> None:
    """Synchronous wrapper for the sleep cycle."""
    try:
        asyncio.run(_encode_short_term_memory())
    except Exception as e:
        console.print(f"[dim red]Hippocampus async error: {e}[/dim red]")


def persist_pipeline_state(
    description: str, route_type: str, domain: str, remaining_steps: list[dict]
) -> None:
    """
    Hippocampus: Saves the current state of the execution pipeline to disk.
    If the system crashes, it can resume from this exact point.
    """
    QUEUE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "original_task": description,
                "route_type": route_type,
                "domain": domain,
                "remaining_steps": remaining_steps,
            },
            f,
            indent=2,
        )


def clear_pipeline_state() -> None:
    """
    Lymphatic System: Clears the execution queue upon graceful termination.
    """
    if QUEUE_FILE_PATH.exists():
        try:
            os.remove(QUEUE_FILE_PATH)
        except OSError:
            pass
