import textwrap
import json
from datetime import datetime
from rich.console import Console
from System.core.paths import ROOT_DIR

console = Console()


def map_system_topology() -> str:
    """
    Generates a UI-agnostic Mermaid diagram of the OS's FULL active topology.
    It dynamically maps the physical file dependencies using the Parietal Lobe.
    """
    try:
        from System.neuroanatomy.cortical.parietal import generate_spatial_map

        topology_file = ROOT_DIR / "Meta" / "system_topology.md"
        topology_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Read Active Motor Cortex State from Proprioceptive Json Registry
        # ⚡ ZERO-DEBT: Decoupled from execution memory loops, reading standard tracking paths
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

        # 2. Read Hippocampus FTS5 State
        db_path = ROOT_DIR / "System" / "config" / "hippocampus.db"
        hippo_state = "Active (Indexed)" if db_path.exists() else "Inactive (Unindexed)"

        # 3. Read Cerebellum Engram Count
        engram_dir = ROOT_DIR / "Meta" / "Engrams"
        engram_count = (
            len(list(engram_dir.glob("*.json"))) if engram_dir.exists() else 0
        )

        # 4. 🧠 DYNAMIC PARIETAL LOBE CRAWL
        system_dir = ROOT_DIR / "System"
        dynamic_mermaid_graph = generate_spatial_map(
            str(system_dir), output_format="mermaid", map_type="code"
        )

        # ⚡ SHIFT-LEFT: Strip the markdown fences from the dynamic graph
        clean_dynamic_graph = dynamic_mermaid_graph.replace(
            "```mermaid\ngraph TD\n", ""
        ).replace("\n```", "")

        # 5. The True Biological Architecture Map (Combined Vitals + Dynamic Crawl)
        mermaid_graph = textwrap.dedent(f"""\
        ```mermaid
        graph TD
            %% --- LIVE AUTONOMIC VITALS ---
            CLI[Neural Interface / CLI] -.-> Interoception[Interoception / Vitals]
            Hippo[(Hippocampus: {hippo_state})]
            Motor[Motor Cortex / Execution] -.-> ActiveProcs[{active_nodes} Active Background Processes]
            Cerebellum[Cerebellum / {engram_count} Engrams]

            %% --- DYNAMIC PHYSICAL FILE TOPOLOGY ---
        {clean_dynamic_graph}
        ```
        """)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"# Brain OS Complete Architecture Map\n*Last generated: {timestamp}*\n\n{mermaid_graph}\n"

        topology_file.write_text(content, encoding="utf-8")
        console.print(
            f"[bold green]🗺️ True Dynamic Topology Map generated at {topology_file.relative_to(ROOT_DIR)}[/bold green]"
        )

        return "Success: System topology successfully mapped."

    except Exception as e:
        return f"Error generating topology map: {str(e)}"
