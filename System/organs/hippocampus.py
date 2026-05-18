import sqlite3
import time
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent
DB_PATH = ROOT_DIR / "System" / "config" / "hippocampus.db"


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
    """
    Maintenance Routine: Completely wipes and rebuilds the SQLite index
    from the flat-file Glass Brain across all major domains.
    """
    console.print("[dim]🧠 Hippocampus: Rebuilding ephemeral search index...[/dim]")
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except PermissionError:
            console.print(
                "[bold red]🛑 Cannot rebuild index: Database is locked by another process.[/bold red]"
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

    # Principle 4 & 5: Indexing all relevant biological and data domains
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
    """
    Searches the index for keywords.
    Principle 3 (Shift-Left): Uses parameterized exact phrase matching to prevent FTS5 injection attacks.
    """
    if not DB_PATH.exists():
        rebuild_index()

    try:
        conn = _get_conn()
        cursor = conn.cursor()

        # Sanitize query for FTS5 exact phrase match (protects against syntax crashes)
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

        # Principle 3 (Token Economics): Return tightly cropped snippets
        return "\n".join(formatted_results)

    except Exception as e:
        return f"Hippocampus recall error: {str(e)}"
