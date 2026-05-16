import textwrap
from datetime import datetime
from rich.console import Console
from System.core.paths import ROOT_DIR

console = Console()


def map_system_topology() -> str:
    """
    Generates a UI-agnostic Mermaid diagram of the OS's current active topology.
    Saves directly to the Meta/ directory for any front-end to parse.
    """
    try:
        topology_file = ROOT_DIR / "Meta" / "system_topology.md"
        topology_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Read Active Motor Cortex State
        try:
            from System.tools.execution import ACTIVE_PROCESSES

            active_nodes = len(ACTIVE_PROCESSES)
        except ImportError:
            active_nodes = 0

        # 2. Read Hippocampus FTS5 State
        db_path = ROOT_DIR / "System" / "config" / "hippocampus.db"
        hippo_state = "Active (Indexed)" if db_path.exists() else "Inactive (Unindexed)"

        # 3. Read Cerebellum Engram Count
        engram_dir = ROOT_DIR / "Meta" / "Engrams"
        engram_count = (
            len(list(engram_dir.glob("*.json"))) if engram_dir.exists() else 0
        )

        # ⚡ SHIFT-LEFT: Construct the Agnostic Mermaid Payload without indentation leakage
        mermaid_graph = textwrap.dedent(f"""\
        ```mermaid
        graph TD
            User((Host Environment)) --> CLI[Neural Interface / CLI]
            CLI --> PFC[Prefrontal Cortex / Dispatcher]

            PFC --> Hippo[(Hippocampus: {hippo_state})]
            PFC --> Wernicke[Wernicke's Area / Semantic Filter]

            PFC --> Motor[Motor Cortex / Execution]
            Motor --> Microglia{{Microglia / Auto-Heal}}
            Motor --> Cerebellum[Cerebellum / {engram_count} Engrams]

            Motor -.-> ActiveProcs[{active_nodes} Active Background Processes]
        ```
        """)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"# Brain OS Architecture Map\n*Last generated: {timestamp}*\n\n{mermaid_graph}\n"

        topology_file.write_text(content, encoding="utf-8")
        console.print(
            f"[bold green]🗺️ Topology Map generated at {topology_file.relative_to(ROOT_DIR)}[/bold green]"
        )

        return (
            "Success: System topology successfully mapped to Meta/system_topology.md."
        )

    except Exception as e:
        return f"Error generating topology map: {str(e)}"
