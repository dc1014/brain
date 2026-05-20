# --- System/tests/limbic/test_graph_backplane.py ---
import json
from pathlib import Path
from System.neuroanatomy.limbic.hippocampus import GraphBackplane
from System.tools.cognitive import traverse_graph


def test_graph_backplane_regex_link_parsing(tmp_path: Path) -> None:
    """Verifies that the markdown graph parser correctly identifies typed relationship links."""
    gb = GraphBackplane(str(tmp_path))

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir()
    test_note = studio_dir / "VentureCore.md"
    test_note.write_text(
        "# VentureCore\n"
        "This project [depends_on::[[Studio/DatabaseService]]]] to persist state data.\n"
        "It also [uses_auth::[[Meta/IdentityServer]]]] for verification checks.\n",
        encoding="utf-8",
    )

    edges = gb.parse_markdown_node(str(test_note))
    assert len(edges) == 2
    assert edges[0]["rel"] == "depends_on"
    assert edges[0]["target"] == "Studio/DatabaseService"
    assert edges[1]["rel"] == "uses_auth"
    assert edges[1]["target"] == "Meta/IdentityServer"


def test_graph_state_json_rebuild_serialization(tmp_path: Path, mocker) -> None:
    """Proves that a state map file is correctly serialized to disk during a rebuild."""
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True, exist_ok=True)
    (studio_dir / "App.md").write_text(
        "Main system logic [calls::[[Studio/Engine]]]].", encoding="utf-8"
    )

    gb = GraphBackplane(str(tmp_path))
    gb.rebuild_graph_state()

    assert Path(gb.graph_file).exists()
    with open(gb.graph_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "Studio/App" in data
    assert data["Studio/App"][0]["rel"] == "calls"
    assert data["Studio/App"][0]["target"] == "Studio/Engine"


def test_traverse_graph_tool_primitive_lookup(tmp_path: Path, mocker) -> None:
    """Validates multi-hop recursive context path resolution via the cognitive tool primitive."""
    mocker.patch("System.tools.cognitive.ROOT_DIR", tmp_path)
    mocker.patch("System.tools.cognitive.is_safe_path", return_value=True)

    # Pre-populate a valid serialized graph state ledger
    brain_dir = tmp_path / ".brain"
    brain_dir.mkdir()
    graph_state = {
        "Studio/Client": [{"rel": "queries", "target": "Studio/Server"}],
        "Studio/Server": [{"rel": "fetches", "target": "Studio/DB"}],
    }
    with open(brain_dir / "graph_state.json", "w", encoding="utf-8") as f:
        json.dump(graph_state, f)

    result = traverse_graph(".", "Studio/Client", max_depth=2)
    assert result.success is True
    assert "Studio/Client -> [queries] -> Studio/Server" in result.output
    assert "Studio/Server -> [fetches] -> Studio/DB" in result.output
