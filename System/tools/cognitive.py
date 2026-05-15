import time
from pathlib import Path
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path


def read_file_signatures(filepath: str) -> str:
    """Reads a code file and returns only its class and function signatures (AST stubs)."""
    try:
        from System.ast_parser import extract_signatures

        target_path: Path = (ROOT_DIR / filepath).resolve()

        if not is_safe_path(target_path):
            return f"SECURITY BLOCK: Access denied to read at {target_path}."
        if not target_path.exists():
            return f"ERROR: File not found at {target_path.relative_to(ROOT_DIR)}"
        if not target_path.is_file():
            return "ERROR: Target is not a file."

        valid_exts = {".py", ".ts", ".tsx", ".js", ".jsx"}
        if target_path.suffix not in valid_exts:
            return f"ERROR: AST stubbing currently only supports {', '.join(valid_exts)} files. Provided: {target_path.suffix}"

        stubs = extract_signatures(str(target_path))
        return (
            f'<document_signatures path="{filepath}">\n{stubs}\n</document_signatures>'
        )
    except Exception as e:
        return f"ERROR: Failed to extract signatures - {str(e)}"


def search_safe_directory(query: str, directory_path: str) -> str:
    """Recursively searches for a string within safe directory bounds, returning telemetry."""
    start_time = time.perf_counter()
    target_path = (ROOT_DIR / directory_path).resolve()

    if target_path == ROOT_DIR:
        return "ERROR: Cannot search the entire OS root. Please narrow your search to a specific safe zone (e.g., 'Studio', 'Personal', 'Professional')."

    if not is_safe_path(target_path):
        return f"SECURITY BLOCK: Cannot search outside allowed directories. Attempted to access {target_path}"

    if not target_path.exists():
        return f"ERROR: Directory '{directory_path}' does not exist."

    results = []
    files_scanned = 0
    ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
    valid_exts = {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".py",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".css",
        ".html",
        ".txt",
    }

    try:
        for filepath in target_path.rglob("*"):
            if filepath.is_file() and filepath.suffix in valid_exts:
                if any(ignored in filepath.parts for ignored in ignore_dirs):
                    continue

                files_scanned += 1
                content = filepath.read_text(errors="ignore")
                if query.lower() in content.lower():
                    results.append(f"- {filepath.relative_to(ROOT_DIR)}")

                    if len(results) >= 15:
                        results.append(
                            "... (Additional results truncated for token limits)"
                        )
                        break

    except Exception as e:
        return f"ERROR: Failed to search directory - {str(e)}"

    duration = time.perf_counter() - start_time
    telemetry = f"[Telemetry: Scanned {files_scanned} files in {duration:.3f} seconds]"

    if not results:
        return f"No matches found for '{query}' in {directory_path}. {telemetry}"

    return (
        f"Found '{query}' in the following files:\n"
        + "\n".join(results)
        + f"\n\n{telemetry}"
    )


def semantic_search(directory: str, query: str) -> str:
    """A deep semantic search using Wernicke's Area."""
    from System.neuroanatomy.cortical.wernicke import filter_semantic_relevance

    raw_results = search_safe_directory(query=query, directory_path=directory)
    return filter_semantic_relevance(query, raw_results)


def search_hippocampus(query: str) -> str:
    """Searches the AI's long-term ephemeral index for code snippets."""
    from System.neuroanatomy.limbic.hippocampus import recall_memory

    return recall_memory(query)


def create_engram_tool(name: str, description: str, commands: str) -> str:
    """Saves a sequence of bash/shell commands into procedural muscle memory."""
    from System.neuroanatomy.autonomic.cerebellum import save_engram

    return save_engram(name, description, commands)


def list_engrams_tool() -> str:
    """Lists all available muscle memory scripts (engrams)."""
    from System.neuroanatomy.autonomic.cerebellum import list_engrams

    return list_engrams()


def execute_engram_tool(name: str, args: str = "") -> str:
    """Instantly executes a learned engram (bash script)."""
    from System.neuroanatomy.autonomic.cerebellum import execute_engram

    return execute_engram(name, args)


def map_spatial_dependencies(
    directory_path: str, output_format: str = "json", map_type: str = "code"
) -> str:
    """PARIETAL LOBE: Generates a spatial dependency graph."""
    from System.neuroanatomy.cortical.parietal_lobe import generate_spatial_map

    target_path = (ROOT_DIR / directory_path).resolve()
    if not is_safe_path(target_path):
        return f"SECURITY BLOCK: Cannot map dependencies outside the workspace ({directory_path})."

    return generate_spatial_map(str(target_path), output_format, map_type)
