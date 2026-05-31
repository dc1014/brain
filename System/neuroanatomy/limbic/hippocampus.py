# --- System/neuroanatomy/limbic/hippocampus.py ---
import re
import json
import hashlib
import asyncio
import sqlite3
import time
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List

from rich.console import Console
from System.core.paths import ROOT_DIR
from System.llm import acompletion
from System.neuroanatomy.systemic.immune_system import vault
from System.core.locks import StateLock
from System.neuroanatomy.autonomic.acc import AnteriorCingulateCortex

# Lazy local import to break top-level circular dependency chains cleanly
from System.neuroanatomy.cortical.wernicke import (
    rank_graph_boosted_results,
    SearchResult,
)

console = Console()

DB_PATH = ROOT_DIR / "System" / "config" / "hippocampus.db"
QUEUE_FILE_PATH = ROOT_DIR / "System" / "execution_queue.json"
QUEUE_LOCK = StateLock(QUEUE_FILE_PATH)
GRAPH_LEDGER_PATH = ROOT_DIR / ".brain" / "graph_state.json"
BELIEFS_FILE_PATH = ROOT_DIR / "Meta" / "Core_Beliefs.md"

# =====================================================================
# 1. EPHEMERAL WORKING MEMORY (SQLite FTS5 + Graph-Boosted RRF)
# =====================================================================


# =====================================================================
# 1. EPHEMERAL WORKING MEMORY (SQLite FTS5 + Graph-Boosted RRF + CAS)
# =====================================================================


def _get_conn():
    """Initializes the FTS5 virtual table and auxiliary stores for fast full-text search."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Enforce a 15-second busy timeout to prevent blocks under high multi-agent concurrency
    conn = sqlite3.connect(DB_PATH, timeout=15.0)

    # ⚡ AUDIT CHECKLIST ITEM: Enable Write-Ahead Logging (WAL) mode for simultaneous read/write
    conn.execute("PRAGMA journal_mode=WAL;")

    # 1. The FTS5 Lexical Search Table
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories
        USING fts5(filepath, content, timestamp UNINDEXED);
    """)

    # 2. The CAS Gatekeeper Registry
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_hashes (
            filepath TEXT PRIMARY KEY,
            content_hash TEXT
        );
    """)

    # 3. The Semantic Abstract Sidecar
    conn.execute("""
        CREATE TABLE IF NOT EXISTS semantic_cache (
            filepath TEXT PRIMARY KEY,
            summary TEXT,
            last_summarized INTEGER
        );
    """)

    conn.commit()
    return conn


def _compute_hash(content: str) -> str:
    """Computes a rapid SHA-256 cryptographic hash of the content string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def encode_memory(filepath: str, content: str) -> bool:
    """
    Surgically updates a single file inside the FTS5 index.
    Utilizes a CAS gatekeeper to abort O(N) processing if the file content is unchanged.
    Returns True if the index was updated, False if skipped due to matching hash.
    """
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        new_hash = _compute_hash(content)

        # 🛡️ THE CAS GATEKEEPER: Check the hash registry
        cursor.execute(
            "SELECT content_hash FROM file_hashes WHERE filepath = ?", (filepath,)
        )
        row = cursor.fetchone()
        if row and row[0] == new_hash:
            conn.close()
            return False  # Abort execution path! Hash matches perfectly.

        # ⚡ O(1) MUTATION: Delete old path, insert fresh state, update hash registry
        cursor.execute("DELETE FROM memories WHERE filepath = ?", (filepath,))
        cursor.execute(
            "INSERT INTO memories (filepath, content, timestamp) VALUES (?, ?, ?)",
            (filepath, content, int(time.time())),
        )
        cursor.execute(
            "INSERT OR REPLACE INTO file_hashes (filepath, content_hash) VALUES (?, ?)",
            (filepath, new_hash),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        console.print(f"[dim red]Hippocampus single encoding error: {e}[/dim red]")
        return False


def rebuild_index() -> None:
    """Incrementally syncs the SQLite index and Supervised Graph Backplane from flat-files using CAS."""
    console.print(
        "[dim]🧠 Hippocampus: Syncing ephemeral search index via CAS gatekeeper...[/dim]"
    )

    # ⚡ FIXED: We no longer unlink/delete the DB file, otherwise we lose our persistent hash registry!

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

    active_filepaths = set()

    for target in core_domains:
        target_dir = ROOT_DIR / target
        if not target_dir.exists():
            continue

        for filepath in target_dir.rglob("*"):
            if filepath.is_file() and filepath.suffix in valid_exts:
                if any(ignored in filepath.parts for ignored in ignore_dirs):
                    continue
                try:
                    rel_path = str(filepath.relative_to(ROOT_DIR).as_posix())
                    active_filepaths.add(rel_path)

                    content = filepath.read_text(encoding="utf-8")
                    new_hash = _compute_hash(content)

                    # 🛡️ Check CAS Gatekeeper
                    cursor.execute(
                        "SELECT content_hash FROM file_hashes WHERE filepath = ?",
                        (rel_path,),
                    )
                    row = cursor.fetchone()

                    if row and row[0] == new_hash:
                        continue  # Hash matches, perfectly cached! Skip DB mutation.

                    # Mutation required
                    cursor.execute(
                        "DELETE FROM memories WHERE filepath = ?", (rel_path,)
                    )
                    cursor.execute(
                        "INSERT INTO memories (filepath, content, timestamp) VALUES (?, ?, ?)",
                        (rel_path, content, int(time.time())),
                    )
                    cursor.execute(
                        "INSERT OR REPLACE INTO file_hashes (filepath, content_hash) VALUES (?, ?)",
                        (rel_path, new_hash),
                    )
                except Exception:
                    continue

    # 🧹 Clean up orphaned files from the index (files in DB but no longer on disk)
    cursor.execute("SELECT filepath FROM file_hashes")
    indexed_paths = {row[0] for row in cursor.fetchall()}
    deleted_paths = indexed_paths - active_filepaths

    for deleted_path in deleted_paths:
        cursor.execute("DELETE FROM memories WHERE filepath = ?", (deleted_path,))
        cursor.execute("DELETE FROM file_hashes WHERE filepath = ?", (deleted_path,))

    conn.commit()
    conn.close()

    try:
        gb = SupervisedGraphBackplane(str(ROOT_DIR))
        gb.supervised_rebuild([])
    except Exception as e:
        console.print(
            f"[dim red]🧠 Hippocampus Graph build bypassed or constrained: {e}[/dim red]"
        )

    console.print(
        "[bold green]✨ Hippocampus index successfully synced from flat files![/bold green]"
    )


def recall_memory(query: str, limit: int = 5) -> str:
    """Performs a two-pass hybrid lookup boosting keyword ranks using knowledge graph density vectors."""
    if not DB_PATH.exists():
        rebuild_index()

    try:
        conn = _get_conn()
        cursor = conn.cursor()
        safe_query = '"' + query.replace('"', '""') + '"'

        # Pass 1: Extract lexical matches with raw FTS5 BM25 ranks
        cursor.execute(
            """
            SELECT filepath, (bm25(memories) * -1.0) AS score
            FROM memories
            WHERE memories MATCH ?
            LIMIT 50
        """,
            (safe_query,),
        )
        raw_rows = cursor.fetchall()
        conn.close()

        if not raw_rows:
            return f"No memories found for '{query}'."

        # Convert records to strict TypedDict contracts to pass mypy analysis contracts safely
        fts_results: List[SearchResult] = [
            {"filepath": str(row[0]), "score": float(row[1]), "boosted_score": None}
            for row in raw_rows
        ]

        # Pass 2: Apply structural lookahead network boost calculation rules via Wernicke
        boosted_nodes = rank_graph_boosted_results(fts_results, str(GRAPH_LEDGER_PATH))
        target_nodes = boosted_nodes[:limit]

        # Pass 3: Extract finalized structured text snippet components for highly integrated matches
        conn = _get_conn()
        cursor = conn.cursor()
        formatted_results = []

        for node in target_nodes:
            path_str = node["filepath"]
            # Enforce an active MATCH condition so SQLite FTS5 correctly injects un-delimited formatting
            cursor.execute(
                """
                SELECT snippet(memories, 1, '[MARK] ', ' [/MARK]', '...', 25)
                FROM memories
                WHERE filepath = ? AND memories MATCH ?
                LIMIT 1
            """,
                (path_str, safe_query),
            )
            snip_row = cursor.fetchone()
            snippet_text = snip_row[0] if snip_row else "..."

            # Defensive unpacking safeguards against NoneType float format errors when files have zero graph connectivity links
            boost_val = node.get("boosted_score")
            final_score = (
                float(boost_val) if boost_val is not None else float(node["score"])
            )

            formatted_results.append(
                f"--- {path_str} (Graph Re-Rank Score: {final_score:.2f}) ---\n...{snippet_text}...\n"
            )

        conn.close()
        return "\n".join(formatted_results)

    except Exception as e:
        return f"Hippocampus recall error: {str(e)}"


# =====================================================================
# 2. RELATIONAL EPISTEMIC STORAGE (The Supervised Graph Backplane Engine)
# =====================================================================


class GraphBackplane:
    """Serverless typed network graph extraction system for linking memory nodes."""

    def __init__(self, vault_path: str) -> None:
        self.vault_path: str = vault_path
        self.graph_file: str = os.path.join(vault_path, ".brain", "graph_state.json")
        self.link_regex: re.Pattern = re.compile(
            r"\[([a-zA-Z_0-9\-]+)::\[\[([^\]]+)\]\]\]"
        )

    def parse_markdown_node(self, file_path: str) -> List[Dict[str, str]]:
        """Extracts typed relationship pairs using structured regex compilation passes."""
        edges: List[Dict[str, str]] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            matches = self.link_regex.findall(content)
            for rel, target in matches:
                edges.append({"rel": rel.strip(), "target": target.strip()})
        except Exception:
            pass
        return edges

    def rebuild_graph_state(self) -> None:
        """Updates the serialized flat JSON map index securely across core workspace zones."""
        graph_map: Dict[str, List[Dict[str, str]]] = {}
        core_domains = ["Studio", "Meta", "Personal", "Professional"]

        for target in core_domains:
            target_path = os.path.join(self.vault_path, target)
            if not os.path.exists(target_path):
                continue

            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".md"):
                        full_path = os.path.join(root, file)
                        relative_slug = (
                            os.path.relpath(full_path, self.vault_path)
                            .replace(".md", "")
                            .replace("\\", "/")
                        )
                        graph_map[relative_slug] = self.parse_markdown_node(full_path)

        os.makedirs(os.path.dirname(self.graph_file), exist_ok=True)
        with open(self.graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_map, f, indent=2)


class SupervisedGraphBackplane(GraphBackplane):
    """Advanced Gated Graph backplane that monitors cognitive tension before committing links."""

    def __init__(self, vault_path: str) -> None:
        super().__init__(vault_path)
        self.acc = AnteriorCingulateCortex()

    def supervised_rebuild(self, interaction_history: List[Dict[str, Any]]) -> None:
        """Gates knowledge graph serialization based on live system tension parameters."""
        tension_report = self.acc.inspect_context_buffer(interaction_history)

        if tension_report.get("action") == "FORCE_STRATEGY_SHIFT":
            console.print(
                "[bold red]⚠️ ACC BLOCK: High cognitive loops detected. Aborting graph write to prevent link pollution.[/bold red]"
            )
            raise RuntimeError(
                "Graph write suspended by Anterior Cingulate Cortex due to high tension score thresholds."
            )

        self.rebuild_graph_state()


# =====================================================================
# 3. SYNAPTIC CONSOLIDATION (Long-Term Domain Memory)
# =====================================================================


async def _compact_heavy_memory(filepath: str, content: str) -> bool:
    """
    Tier 1 Hybrid Semantic Compactor: Generates a low-entropy abstract of heavy files
    and stores it in the Sidecar Registry to protect LLM context windows.
    Returns True if successfully compacted, False otherwise.
    """
    # ⚡ P1 FIX: Respect the DNA's fast model preference if Gemini isn't available
    from System.core.dna import get_dna_config

    model = (
        "gemini/gemini-2.5-flash"
        if vault.get_api_key_for_model("gemini/")
        else get_dna_config().get("models", {}).get("fast", "openai/gpt-4o-mini")
    )
    api_key = vault.get_api_key_for_model(model)

    if not api_key:
        console.print(
            "[dim yellow]⚠️ Semantic Compactor: No API key found. Skipping compression.[/dim yellow]"
        )
        return False

    console.print(f"[dim blue]🧠 Compacting heavy memory: {filepath}...[/dim blue]")

    prompt = (
        "You are the internal Semantic Compactor for CoreTex OS. "
        "Your job is to protect the execution agent's context window. "
        "Read the following file content and generate a highly compressed, 2-3 sentence technical summary. "
        "Focus purely on architectural purpose, core functions, and state. Do not use filler words.\n\n"
        f"FILE ({filepath}):\n{content[:15000]}"  # Cap at 15k chars to prevent massive context blows here
    )

    try:
        response = await acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            api_key=api_key,
        )
        summary = (
            response.choices[0].message.content.strip()
            if response.choices[0].message.content
            else ""
        )

        # Save to the Semantic Sidecar
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO semantic_cache (filepath, summary, last_summarized) VALUES (?, ?, ?)",
            (filepath, summary, int(time.time())),
        )
        conn.commit()
        conn.close()

        console.print(
            f"[dim green]✅ Compacted and safely stored sidecar for {filepath}[/dim green]"
        )
        return True

    except Exception as e:
        console.print(f"[dim red]⚠️ Compaction failed for {filepath}: {e}[/dim red]")
        return False


def _extract_and_update_beliefs(recent_logs: str = "") -> None:
    """
    The Epistemologist: Extracts long-term semantic beliefs, user preferences, and identity facts.
    Treats Meta/Core_Beliefs.md as the source of truth for WHO the user is.
    """
    from System.core.paths import ROOT_DIR
    import asyncio
    from System.llm import acompletion
    from System.neuroanatomy.systemic.immune_system import vault
    from System.core.dna import get_dna_config

    beliefs_file = ROOT_DIR / "Meta" / "Core_Beliefs.md"
    current_beliefs = ""
    if beliefs_file.exists():
        current_beliefs = beliefs_file.read_text(encoding="utf-8")
    else:
        current_beliefs = "*(CoreTex will autonomously learn your preferences, tech stack, and identity over time and log them here).*"

    if not recent_logs:
        log_path = ROOT_DIR / "System" / "logs" / "experiment_log.md"
        if log_path.exists():
            try:
                recent_logs = log_path.read_text(encoding="utf-8")[-3000:]
            except Exception:
                recent_logs = "No recent logs available."
        else:
            recent_logs = "No recent logs available."

    epistemology_prompt = (
        f"You are the Hippocampus. Your job is to extract long-term semantic facts about the user, their environment, and their preferences.\n"
        f"CURRENT BELIEFS (`Core_Beliefs.md`):\n{current_beliefs}\n\n"
        f"RECENT LOGS (Today's Actions):\n{recent_logs}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. Review the recent logs for any persistent facts (e.g., 'User prefers Pytest', 'Project uses React', 'User is a roofer').\n"
        f"2. Merge these new facts into the CURRENT BELIEFS. Do NOT extract temporary tasks or goals.\n"
        f"3. Keep it as a clean, bulleted Markdown list. Discard redundant information.\n"
        f"OUTPUT EXACTLY the new raw markdown for `Core_Beliefs.md` and nothing else. Do not use code block markers."
    )

    async def _fetch():
        model = get_dna_config().get("models", {}).get("fast", "openai/gpt-4o-mini")
        routed_model, api_key = vault.resolve_routing(model)

        if not api_key:
            return None

        kwargs = {
            "model": routed_model,
            "messages": [{"role": "user", "content": epistemology_prompt}],
            "temperature": 0.1,
            "api_key": api_key,
        }
        gateway_url = vault.get_secret("GATEWAY_BASE_URL")
        if gateway_url:
            kwargs["api_base"] = gateway_url

        response = await acompletion(**kwargs)
        return (
            response.choices[0].message.content.strip()
            if response.choices[0].message.content
            else ""
        )

    try:
        result = asyncio.run(_fetch())
        if result and len(result) > 10:
            cleaned = result.replace("```markdown", "").replace("```", "").strip()
            beliefs_file.parent.mkdir(parents=True, exist_ok=True)
            beliefs_file.write_text(cleaned, encoding="utf-8")
            console.print(
                "[bold green]🧠 Hippocampus: Core Beliefs updated.[/bold green]"
            )
    except Exception as e:
        console.print(
            f"[dim red]Hippocampus belief update failed silently: {e}[/dim red]"
        )


def _lint_and_sync_goals() -> None:
    """
    The Teleologist: Zero-token Python tracker that auto-tags new goals
    and deterministically checks off completed ones based on execution logs.
    """
    from System.core.paths import ROOT_DIR

    goals_file = ROOT_DIR / "Meta" / "Goals.md"
    log_file = ROOT_DIR / "logs" / "agent_interactions.jsonl"

    if not goals_file.exists():
        return

    console.print("[dim]🧠 Hippocampus: Linting Master Goals state machine...[/dim]")

    completed_threads = set()
    if log_file.exists():
        try:
            lines = log_file.read_text(encoding="utf-8").splitlines()[-500:]
            for line in lines:
                try:
                    data = json.loads(line)
                    thread = data.get("goal_thread")
                    response = data.get("response", "")

                    if thread and "API/Execution Error:" not in response:
                        completed_threads.add(thread)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

    try:
        content = goals_file.read_text(encoding="utf-8")
        new_lines = []
        lines = content.split("\n")
        goal_regex = re.compile(r"(#goal/[a-zA-Z0-9_-]+)")

        for line in lines:
            stripped = line.lstrip()
            is_active_task = stripped.startswith("- [ ]") or stripped.startswith(
                "- [-]"
            )

            if is_active_task:
                match = goal_regex.search(line)
                if not match:
                    new_id = f"#goal/{uuid.uuid4().hex[:4]}"
                    line = f"{line} {new_id}"
                    thread_id = new_id
                else:
                    thread_id = match.group(1)

                if thread_id in completed_threads:
                    line = line.replace("- [ ]", "- [x]", 1).replace(
                        "- [-]", "- [x]", 1
                    )

            new_lines.append(line)

        goals_file.write_text("\n".join(new_lines), encoding="utf-8")
        console.print(
            "[bold green]🎯 Hippocampus: Master Goals synced successfully. Zero tokens burned.[/bold green]"
        )

    except Exception as e:
        console.print(f"[dim red]Goal sync failed silently: {e}[/dim red]")


def get_core_beliefs() -> str:
    """Retrieves the synthesized Core Beliefs preamble."""
    if BELIEFS_FILE_PATH.exists():
        return BELIEFS_FILE_PATH.read_text(encoding="utf-8").strip()
    return ""


async def _encode_short_term_memory() -> None:
    """Summarizes active JSONL ledgers into dense, long-term markdown memories by DOMAIN."""
    ledgers = list(ROOT_DIR.rglob("agent_interactions.jsonl"))
    domain_events: Dict[str, List[str]] = {}

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
            f"You are the Hippocampus of CoreTex OS. Summarize the following recent agent interactions for the {domain} domain into a brief, "
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
            summary = (
                str(response.choices[0].message.content).strip()
                if response.choices[0].message.content
                else ""
            )

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

    async def _run_all():
        await _encode_short_term_memory()

    try:
        # Run async first, then run sequential sync passes
        asyncio.run(_run_all())
        _lint_and_sync_goals()  # ⚡ Python Goal Sync (Teleology)
        _extract_and_update_beliefs()  # ⚡ LLM Beliefs Extraction (Epistemology)
    except Exception as e:
        console.print(f"[dim red]Hippocampus async error: {e}[/dim red]")


def run_semantic_compaction_sweep() -> None:
    """Scans the working memory for heavy files and asynchronously compacts them."""
    console.print("[dim]🧠 Initiating Sleep Cycle: Semantic Compaction Sweep...[/dim]")

    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.filepath, m.content
        FROM memories m
        LEFT JOIN semantic_cache s ON m.filepath = s.filepath
        WHERE length(m.content) > 3000
        AND (s.summary IS NULL OR m.timestamp > s.last_summarized)
        LIMIT 5
    """)
    heavy_files = cursor.fetchall()
    conn.close()

    if not heavy_files:
        console.print(
            "[dim]🧠 Semantic Compaction: All heavy files are currently optimized.[/dim]"
        )
        return

    async def compact_all():
        tasks = [
            _compact_heavy_memory(filepath, content)
            for filepath, content in heavy_files
        ]
        await asyncio.gather(*tasks)

    try:
        asyncio.run(compact_all())
    except Exception as e:
        console.print(f"[dim red]Semantic sweep async error: {e}[/dim red]")
