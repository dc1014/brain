from System.neuroanatomy.pathways.synaptic_routing import configure_synaptic_routing


def test_configure_synaptic_routing_no_server(tmp_path, monkeypatch):
    """Proves the reflex safely injects a new server block into a clean Vite config."""
    monkeypatch.setattr(
        "System.neuroanatomy.pathways.synaptic_routing.ROOT_DIR", tmp_path
    )
    project_dir = tmp_path / "Studio" / "TestProject"
    project_dir.mkdir(parents=True)

    vite_file = project_dir / "vite.config.ts"
    vite_file.write_text(
        "export default defineConfig({ plugins: [react()] })", encoding="utf-8"
    )

    res = configure_synaptic_routing("TestProject", 8000)
    assert "Success" in res

    content = vite_file.read_text(encoding="utf-8")
    assert "server:" in content
    assert "proxy:" in content
    assert "localhost:8000" in content


def test_configure_synaptic_routing_existing_server(tmp_path, monkeypatch):
    """Proves the reflex safely injects the proxy into an already existing server block."""
    monkeypatch.setattr(
        "System.neuroanatomy.pathways.synaptic_routing.ROOT_DIR", tmp_path
    )
    project_dir = tmp_path / "Studio" / "TestProject"
    project_dir.mkdir(parents=True)

    vite_file = project_dir / "vite.config.ts"
    vite_file.write_text(
        "export default defineConfig({\n  server: {\n    port: 3000\n  }\n})",
        encoding="utf-8",
    )

    res = configure_synaptic_routing("TestProject", 8000)
    assert "Success" in res

    content = vite_file.read_text(encoding="utf-8")
    assert "proxy:" in content
    assert "localhost:8000" in content


def test_configure_synaptic_routing_already_exists(tmp_path, monkeypatch):
    """Proves the reflex skips injection if a proxy already exists."""
    monkeypatch.setattr(
        "System.neuroanatomy.pathways.synaptic_routing.ROOT_DIR", tmp_path
    )
    project_dir = tmp_path / "Studio" / "TestProject"
    project_dir.mkdir(parents=True)

    vite_file = project_dir / "vite.config.ts"
    vite_file.write_text(
        "export default defineConfig({ server: { proxy: {} } })", encoding="utf-8"
    )

    res = configure_synaptic_routing("TestProject", 8000)
    assert "already established" in res
