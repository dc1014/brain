# --- System/tools/topology.py ---
import json
import ast
from datetime import datetime
from rich.console import Console
from System.core.paths import ROOT_DIR

console = Console()


def map_system_topology(format_type: str) -> str:
    """
    Dynamic Neuroanatomy Topology Explorer.

    Recursively audits the Abstract Syntax Tree (AST) of all active brain modules
    to map biological interconnections while strictly muting external package,
    utility, and test footprint clutter.

    Args:
        format_type (str): Format specifier. Expects "mermaid".
    """
    try:
        topology_file = ROOT_DIR / "Meta" / "system_topology.md"
        topology_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Read Active Telemetry & Functional Vitals
        state_file = ROOT_DIR / "Meta" / "Proprioception" / "motor_state.json"
        active_nodes = 0
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                    if isinstance(state_data, dict):
                        active_nodes = len(state_data)
            except Exception:
                active_nodes = 0

        db_path = ROOT_DIR / "System" / "config" / "hippocampus.db"
        hippo_state = "Indexed" if db_path.exists() else "Unindexed"

        engram_dir = ROOT_DIR / "Meta" / "Engrams"
        engram_count = (
            len(list(engram_dir.glob("*.json"))) if engram_dir.exists() else 0
        )

        # 2. Dynamic Component Discovery Map
        neuro_dir = ROOT_DIR / "System" / "neuroanatomy"
        if not neuro_dir.exists():
            return (
                "Error: System/neuroanatomy directory does not exist physical reality."
            )

        subgraphs: dict[str, list[str]] = {}
        all_nodes: dict[str, dict[str, str]] = {}
        edges: set[tuple[str, str]] = set()

        # Group discovered modules cleanly by their biological region subdirectories
        for folder in sorted(neuro_dir.iterdir()):
            if folder.is_dir() and not folder.name.startswith("__"):
                subgraphs[folder.name] = []

                for file_path in sorted(folder.glob("*.py")):
                    if file_path.name.startswith("__") or "test_" in file_path.name:
                        continue

                    component_key = file_path.stem
                    node_id = f"{folder.name}_{component_key}"
                    display_label = component_key.replace("_", " ").title()

                    all_nodes[node_id] = {"label": display_label, "folder": folder.name}
                    subgraphs[folder.name].append(node_id)

                    # 3. Deep AST Analysis: Extract Inter-Module Signal Lines
                    try:
                        file_content = file_path.read_text(encoding="utf-8")
                        tree = ast.parse(file_content)

                        for ast_node in ast.walk(tree):
                            # Trap style syntax: from System.neuroanatomy.cortical.prefrontal import ...
                            if isinstance(ast_node, ast.ImportFrom) and ast_node.module:
                                if "System.neuroanatomy" in ast_node.module:
                                    parts = ast_node.module.split(".")
                                    if len(parts) >= 4:
                                        target_folder = parts[2]
                                        target_module = parts[3]
                                        target_id = f"{target_folder}_{target_module}"
                                        edges.add((node_id, target_id))

                            # Trap style syntax: import System.neuroanatomy.limbic.thalamus
                            elif isinstance(ast_node, ast.Import):
                                for alias in ast_node.names:
                                    if alias.name.startswith("System.neuroanatomy"):
                                        parts = alias.name.split(".")
                                        if len(parts) >= 4:
                                            target_folder = parts[2]
                                            target_module = parts[3]
                                            target_id = (
                                                f"{target_folder}_{target_module}"
                                            )
                                            edges.add((node_id, target_id))
                    except Exception:
                        pass  # Skip corrupted or non-parseable file artifacts safely

        # 4. Construct Syntax-Validated Mermaid Layout Graph Strings
        mermaid_lines = [
            "graph TB",
            "    %% --- Subsystem Stylizations ---",
            "    classDef cortical fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px,color:#01579b;",
            "    classDef limbic fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px,color:#4a148c;",
            "    classDef autonomic fill:#ffe0b2,stroke:#ff9800,stroke-width:2px,color:#e65100;",
            "    classDef systemic fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#1b5e20;",
            "    classDef pathways fill:#eceff1,stroke:#607d8b,stroke-width:2px,color:#263238;",
            "    classDef sensory fill:#fffde7,stroke:#fbc02d,stroke-width:1px,color:#f57f17;",
            "    classDef peripheral fill:#fafafa,stroke:#9e9e9e,stroke-width:1px,color:#212121;",
        ]

        # Map Subgraph Containers Dynamically
        for folder_name, nodes in subgraphs.items():
            if not nodes:
                continue
            folder_title = folder_name.replace("_", " ").title()
            mermaid_lines.append(
                f"    subgraph {folder_name}_sub [{folder_title} Subsystems]"
            )
            for n_id in nodes:
                label = all_nodes[n_id]["label"]
                mermaid_lines.append(f'        {n_id}["{label}"]')
            mermaid_lines.append("    end")

            style_class = (
                folder_name
                if folder_name
                in [
                    "cortical",
                    "limbic",
                    "autonomic",
                    "systemic",
                    "pathways",
                    "sensory",
                ]
                else "peripheral"
            )
            node_list = ",".join(nodes)
            mermaid_lines.append(f"    class {node_list} {style_class};")

        # Connect Verified Functional Channels
        mermaid_lines.append("    %% --- Functional Neurological Interconnections ---")
        for src, tgt in sorted(edges):
            if src in all_nodes and tgt in all_nodes:
                if src != tgt:
                    mermaid_lines.append(f"    {src} --> {tgt}")

        mermaid_graph_string = "\n".join(mermaid_lines)

        # 5. Format and Export to Pristine Markdown File Sequentially
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        markdown_lines = [
            "# Brain OS Dynamic Neuroanatomy Topology Map",
            f"*Generated dynamically via AST Explorer on: {timestamp}*",
            "",
            "## System Interconnections Reference",
            "This map details the functional data interactions and logical couplings between core neurological brain subsystems.",
            "It is compiled dynamically by scanning the Abstract Syntax Tree (AST) of the active codebase modules, completely filtering out third-party framework dependencies, flat utilities, and testing modules.",
            "",
            "```mermaid",
            mermaid_graph_string,
            "```",
            "",
            "## Active Subsystem Summary",
            f"- **Persistence Index Layer**: Hippocampus FTS5 database maps are current (`{hippo_state}`).",
            f"- **Muscle Memory Cache**: Cerebellum holding `{engram_count}` active zero-token engrams.",
            f"- **Autonomic Center**: Medulla Oblongata supervising `{active_nodes}` live process threads.",
        ]

        content = "\n".join(markdown_lines) + "\n"
        topology_file.write_text(content, encoding="utf-8")

        console.print(
            f"[bold green]🗺️ True Dynamic AST Explorer Map generated successfully at {topology_file.relative_to(ROOT_DIR)}[/bold green]"
        )

        return "Success: System topology successfully mapped."

    except Exception as e:
        return f"Error generating topology map: {str(e)}"
