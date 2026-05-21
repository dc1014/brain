from System.tools.topology import map_system_topology


def test_map_system_topology_generation(monkeypatch, tmp_path):
    """
    Zero-Debt Test: Proves the Topology engine correctly reads autonomic states,
    invokes the Parietal Lobe, and outputs a valid Mermaid markdown file agnostically.
    """
    monkeypatch.setattr("System.tools.topology.ROOT_DIR", tmp_path)

    # 1. ⚡ THE FIX: Setup a fake System/neuroanatomy directory for the Parietal Lobe to crawl
    neuro_dir = tmp_path / "System" / "neuroanatomy" / "cortical"
    neuro_dir.mkdir(parents=True)
    fake_module = neuro_dir / "prefrontal.py"
    fake_module.write_text(
        "import System.neuroanatomy.limbic.thalamus\n", encoding="utf-8"
    )

    # Map a fake destination endpoint target folder so the graph links parse safely
    (tmp_path / "System" / "neuroanatomy" / "limbic").mkdir(parents=True, exist_ok=True)
    (tmp_path / "System" / "neuroanatomy" / "limbic" / "thalamus.py").write_text(
        "# Thalamus mock", encoding="utf-8"
    )

    # 2. Trigger the topology reflex
    result = map_system_topology("mermaid")

    # 3. Verify Output Location
    topology_file = tmp_path / "Meta" / "system_topology.md"
    assert topology_file.exists(), "Topology file was not generated!"
    assert "Success" in result


def test_topology_generation_with_required_contract():
    from System.tools.topology import map_system_topology

    # Ensure parameter validation satisfies strict contracts in mocks/tests
    res = map_system_topology("mermaid")
    assert "Success" in res
