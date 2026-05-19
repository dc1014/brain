from System.tools.topology import map_system_topology


def test_map_system_topology_generation(monkeypatch, tmp_path):
    """
    Zero-Debt Test: Proves the Topology engine correctly reads autonomic states,
    invokes the Parietal Lobe, and outputs a valid Mermaid markdown file agnostically.
    """
    monkeypatch.setattr("System.tools.topology.ROOT_DIR", tmp_path)

    # 1. Setup a fake System directory for the Parietal Lobe to crawl
    system_dir = tmp_path / "System"
    system_dir.mkdir(parents=True)
    fake_module = system_dir / "module_a.py"
    fake_module.write_text("import module_b\n", encoding="utf-8")

    # 2. Trigger the topology reflex
    result = map_system_topology("mermaid")  # ⚡ THE FIX: Pass the required parameter!

    # 3. Verify Output Location
    topology_file = tmp_path / "Meta" / "system_topology.md"
    assert topology_file.exists(), "Topology file was not generated!"
    assert "Success" in result

    # 4. Verify Agnostic Content Payload & Dynamic Crawl
    content = topology_file.read_text(encoding="utf-8")

    assert "```mermaid\ngraph TD" in content, "Indentation leaked into the Markdown!"
    assert "Brain OS Complete Architecture Map" in content

    # Assert that the autonomic vitals injected correctly
    assert "Active Background Processes" in content
    assert "Engrams" in content

    # Assert that the dynamic Parietal Lobe crawl injected correctly
    assert "module_a.py" in content
    assert "module_b" in content
