import time
from pathlib import Path
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path
from System.core.schemas import ExecutionResult


def read_file_signatures(filepath: str) -> ExecutionResult:
    """Reads a code file and returns only its class and function signatures (AST stubs)."""
    try:
        from System.ast_parser import extract_signatures

        target_path: Path = (ROOT_DIR / filepath).resolve()

        if not is_safe_path(target_path):
            reason = f"SECURITY BLOCK: Access denied to read at {target_path}."
            return ExecutionResult(success=False, output=reason, block_reason=reason)
        if not target_path.exists():
            reason = f"ERROR: File not found at {target_path.relative_to(ROOT_DIR)}"
            return ExecutionResult(success=False, output=reason, block_reason=reason)
        if not target_path.is_file():
            reason = "ERROR: Target is not a file."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        valid_exts = {".py", ".ts", ".tsx", ".js", ".jsx"}
        if target_path.suffix not in valid_exts:
            reason = f"ERROR: AST stubbing currently only supports {', '.join(valid_exts)} files. Provided: {target_path.suffix}"
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        stubs = extract_signatures(str(target_path))
        return ExecutionResult(
            success=True,
            output=f'<document_signatures path="{filepath}">\n{stubs}\n</document_signatures>',
        )
    except Exception as e:
        reason = f"ERROR: Failed to extract signatures - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def search_safe_directory(query: str, directory_path: str) -> ExecutionResult:
    """Recursively searches for a string within safe directory bounds, returning telemetry."""
    start_time = time.perf_counter()
    target_path = (ROOT_DIR / directory_path).resolve()

    if target_path == ROOT_DIR:
        reason = "ERROR: Cannot search the entire OS root. Please narrow your search to a specific safe zone (e.g., 'Studio', 'Personal', 'Professional')."
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    if not is_safe_path(target_path):
        reason = f"SECURITY BLOCK: Cannot search outside allowed directories. Attempted to access {target_path}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    if not target_path.exists():
        reason = f"ERROR: Directory '{directory_path}' does not exist."
        return ExecutionResult(success=False, output=reason, block_reason=reason)

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
        reason = f"ERROR: Failed to search directory - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    duration = time.perf_counter() - start_time
    telemetry = f"[Telemetry: Scanned {files_scanned} files in {duration:.3f} seconds]"

    if not results:
        return ExecutionResult(
            success=True,
            output=f"No matches found for '{query}' in {directory_path}. {telemetry}",
        )

    return ExecutionResult(
        success=True,
        output=f"Found '{query}' in the following files:\n"
        + "\n".join(results)
        + f"\n\n{telemetry}",
    )


def semantic_search(directory: str, query: str) -> ExecutionResult:
    """A deep semantic search using Wernicke's Area."""
    from System.neuroanatomy.cortical.wernicke import filter_semantic_relevance

    raw_results = search_safe_directory(query=query, directory_path=directory)
    output = filter_semantic_relevance(query, raw_results.output)
    if output.startswith("ERROR") or output.startswith("SECURITY BLOCK"):
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)


def search_hippocampus(query: str) -> ExecutionResult:
    """Searches the AI's long-term ephemeral index for code snippets."""
    from System.neuroanatomy.limbic.hippocampus import recall_memory

    output = recall_memory(query)
    return ExecutionResult(success=True, output=output)


def create_engram_tool(
    name: str, description: str, commands: list[str]
) -> ExecutionResult:
    """Saves a sequence of bash/shell commands into procedural muscle memory."""
    from System.neuroanatomy.autonomic.cerebellum import create_engram

    output = create_engram(name, description, commands)
    if "Failed" in output or "Error" in output:
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)


def list_engrams_tool() -> ExecutionResult:
    """Lists all available muscle memory scripts (engrams)."""
    from System.neuroanatomy.autonomic.cerebellum import list_engrams

    output = list_engrams()
    return ExecutionResult(success=True, output=output)


def execute_engram_tool(
    name: str, target_dir: str, params: dict | None = None
) -> ExecutionResult:
    """Instantly executes a learned engram (bash script)."""
    from System.neuroanatomy.autonomic.cerebellum import execute_engram

    output = execute_engram(name, target_dir, params)
    if (
        "failed" in output.lower()
        or "error" in output.lower()
        or "SECURITY BLOCK" in output
    ):
        return ExecutionResult(success=False, output=output, block_reason=output)
    return ExecutionResult(success=True, output=output)


def map_spatial_dependencies(
    directory_path: str, output_format: str = "json", map_type: str = "code"
) -> ExecutionResult:
    """PARIETAL LOBE: Generates a spatial dependency graph."""
    from System.neuroanatomy.cortical.parietal_lobe import generate_spatial_map

    target_path = (ROOT_DIR / directory_path).resolve()

    if not is_safe_path(target_path):
        reason = f"SECURITY BLOCK: Cannot map dependencies outside the workspace ({directory_path})."
        return ExecutionResult(success=False, output=reason, block_reason=reason)

    output = generate_spatial_map(str(target_path), output_format, map_type)
    return ExecutionResult(success=True, output=output)


def configure_synaptic_routing_tool(
    project_name: str, backend_port: int, api_prefix: str = "/api"
) -> ExecutionResult:
    """Standardized tool wrapper for dynamic Vite proxy injection."""
    from System.neuroanatomy.pathways.synaptic_routing import configure_synaptic_routing

    output = configure_synaptic_routing(project_name, backend_port, api_prefix)
    success = "Success" in output or "already established" in output
    return ExecutionResult(
        success=success, output=output, block_reason="" if success else output
    )


def map_system_topology_tool() -> ExecutionResult:
    """Standardized tool wrapper for the topology engine."""
    from System.tools.topology import map_system_topology

    output = map_system_topology(format_type="graphviz")
    success = "Success" in output
    return ExecutionResult(
        success=success, output=output, block_reason="" if success else output
    )


async def transmit_telepathy(
    target_node_id: str, action: str, target: str = "", protocol: str = "acp"
) -> str:
    """
    Commands an external AI framework or peer Brain OS node via the Exocortex.
    Use this to delegate tasks to OpenClaw, Hermes, or read Public resources from peer brains.

    Args:
        target_node_id: The ID of the external node (e.g., 'openclaw_local', 'hermes_1').
        action: The MCP action to trigger (e.g., 'EXECUTE_ENGRAM', 'READ_RESOURCE').
        target: The specific engram name or resource file to target.
    """
    from System.neuroanatomy.cortical.exocortex import Exocortex

    exo = Exocortex()
    return await exo.transmit_outbound_pulse(target_node_id, action, target, protocol)
