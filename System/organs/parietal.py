import os
import re
from pathlib import Path
from typing import Dict, List, Set


def _detect_vertigo(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Runs a DFS to detect cycles (circular dependencies) in the spatial map."""
    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    path: List[str] = []
    cycles: List[List[str]] = []

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for raw_neighbor in graph.get(node, []):
            # Resolve namespace: 'b' -> 'b.py' or 'utils/b.py'
            # We look for any node in the graph that ends with the neighbor's exact name
            neighbor = next(
                (
                    k
                    for k in graph.keys()
                    if k.endswith(f"{raw_neighbor}.py")
                    or k.endswith(f"{raw_neighbor}.ts")
                    or k == raw_neighbor
                ),
                raw_neighbor,
            )

            if neighbor not in visited:
                if (
                    neighbor in graph
                ):  # Only recurse if the neighbor is a local file in the graph!
                    dfs(neighbor)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:].copy() + [neighbor])

        rec_stack.remove(node)
        path.pop()

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def generate_spatial_map(
    directory: str, output_format: str = "json", map_type: str = "code"
) -> str:
    """
    The Parietal Lobe: Generates a 3D spatial map of the environment.
    map_type="code": Traces imports to build software architecture (JSON/Mermaid).
    map_type="notes": Traces [[Wikilinks]] to build a knowledge graph of thoughts.
    """
    import json

    target_dir = Path(directory).resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        return f"Error: Directory not found: {directory}"

    spatial_map: Dict[str, List[str]] = {}
    ignored_dirs = {".git", "__pycache__", "node_modules", ".venv", "dist", "build"}

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]

        for file in files:
            file_path = Path(root) / file
            rel_path = str(file_path.relative_to(target_dir)).replace("\\", "/")

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                deps = []

                # MODE 1: CODE TOPOLOGY
                if map_type == "code" and file.endswith(
                    (".py", ".ts", ".js", ".tsx", ".jsx")
                ):
                    import_pattern = re.compile(
                        r'^(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+)|import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"])',
                        re.MULTILINE,
                    )
                    for match in import_pattern.finditer(content):
                        found = [m for m in match.groups() if m]
                        if found:
                            deps.append(found[0].replace("./", "").replace("../", ""))
                    if deps:
                        spatial_map[rel_path] = list(set(deps))

                # MODE 2: THOUGHT TOPOLOGY (OBSIDIAN KNOWLEDGE GRAPH)
                elif map_type == "notes" and file.endswith(".md"):
                    # Find all Obsidian [[Wikilinks]]
                    wiki_pattern = re.compile(r"\[\[(.*?)\]\]")
                    for match in wiki_pattern.finditer(content):
                        # Extract the exact link name, stripping out aliases like [[Note|Alias]]
                        link = match.group(1).split("|")[0]
                        deps.append(link)
                    if deps:
                        # Strip the .md extension for cleaner graph reading
                        clean_name = file.replace(".md", "")
                        spatial_map[clean_name] = list(set(deps))

            except Exception:
                pass

    # 2. Format Outputs
    if output_format == "vertigo_check":
        cycles = _detect_vertigo(spatial_map)
        if not cycles:
            return (
                "[PARIETAL LOBE: STRUCTURALLY SOUND] No circular dependencies detected."
            )
        warning = "[VERTIGO DETECTED] Circular dependencies found:\n"
        for i, cycle in enumerate(cycles):
            warning += f"{i + 1}. {' -> '.join(cycle)}\n"
        return warning

    elif output_format == "mermaid":
        mermaid = "```mermaid\ngraph TD\n"
        for node, edges in spatial_map.items():
            safe_node = node.replace(".", "_").replace("/", "_").replace(" ", "_")
            for edge in edges:
                safe_edge = edge.replace(".", "_").replace("/", "_").replace(" ", "_")
                mermaid += f'    {safe_node}["{node}"] --> {safe_edge}["{edge}"]\n'
        mermaid += "```"
        return mermaid

    else:  # Default JSON
        title = "KNOWLEDGE GRAPH" if map_type == "notes" else "CODE SPATIAL MAP"
        return f"[PARIETAL LOBE {title}]\n" + json.dumps(spatial_map, indent=2)
