from System.tools.topology import map_system_topology


def test_map_system_topology_generation(monkeypatch, tmp_path):
    """
    Zero-Debt Test: Proves the Topology engine correctly reads autonomic states
    and outputs a valid, left-aligned Mermaid markdown file agnostically.
    """
    monkeypatch.setattr("System.tools.topology.ROOT_DIR", tmp_path)

    # 1. Trigger the topology reflex
    result = map_system_topology()

    # 2. Verify Output Location
    topology_file = tmp_path / "Meta" / "system_topology.md"
    assert topology_file.exists(), "Topology file was not generated!"
    assert "Success" in result

    # 3. Verify Agnostic Content Payload & Strict Formatting
    content = topology_file.read_text(encoding="utf-8")

    # Check that textwrap.dedent successfully aligned the codeblocks
    assert "```mermaid\ngraph TD" in content, "Indentation leaked into the Markdown!"
    # ⚡ ZERO-DEBT FIX: Match the updated title exactly
    assert "Brain OS Complete Architecture Map" in content
    assert "Prefrontal Cortex" in content
    assert "Motor Cortex" in content
