from System.neuroanatomy.sensory.somatosensory import process_sensory_event


def test_somatosensory_cortex_local_reflex(monkeypatch, tmp_path):
    """Proves the cortex correctly routes local file events to the syntax linter reflex."""

    # 1. Map the Cortex ROOT_DIR to the safe test environment
    monkeypatch.setattr("System.neuroanatomy.sensory.somatosensory.ROOT_DIR", tmp_path)

    printed_messages = []
    monkeypatch.setattr(
        "System.neuroanatomy.sensory.somatosensory.console.print",
        lambda msg: printed_messages.append(str(msg)),
    )

    # Mock the tool so we don't actually run ruff in the test suite
    monkeypatch.setattr(
        "System.tools.analyze_safe_syntax", lambda path: "✅ Linter passed"
    )

    # 2. Fire a mock nerve impulse using a valid sandbox path
    fake_file = tmp_path / "Studio" / "main.py"
    process_sensory_event("local_fs", "file_modified", {"filepath": str(fake_file)})

    assert any("saved cleanly" in msg for msg in printed_messages), (
        "The syntax reflex did not fire!"
    )


def test_somatosensory_cortex_webhook_extensibility(monkeypatch):
    """Proves the cortex is prepared to receive future webhook events safely."""

    printed_messages = []
    monkeypatch.setattr(
        "System.neuroanatomy.sensory.somatosensory.console.print",
        lambda msg: printed_messages.append(str(msg)),
    )

    # Fire a mock remote webhook
    process_sensory_event("webhook", "github_push", {"repo": "forge"})

    assert any("received remote webhook" in msg for msg in printed_messages)


def test_somatosensory_cortex_ast_reflex(monkeypatch, tmp_path):
    """Proves the cortex extracts AST signatures and updates the Meta/AST map."""

    monkeypatch.setattr("System.neuroanatomy.sensory.somatosensory.ROOT_DIR", tmp_path)

    printed_messages = []
    monkeypatch.setattr(
        "System.neuroanatomy.sensory.somatosensory.console.print",
        lambda msg: printed_messages.append(str(msg)),
    )

    # Mock the AST extractor so we don't need real code
    monkeypatch.setattr(
        "System.ast_parser.extract_signatures", lambda path: "def mock_func(): pass"
    )

    # Fire the nerve impulse for a Python file
    fake_file = tmp_path / "Studio" / "test_module.py"
    process_sensory_event("local_fs", "file_modified", {"filepath": str(fake_file)})

    # Verify the print statement fired
    assert any("AST Map updated" in msg for msg in printed_messages)

    # Verify the physical file was created in the correct place
    ast_dir = tmp_path / "Meta" / "AST"
    ast_file = ast_dir / "Studio_test_module.py.md"

    assert ast_file.exists(), "The AST shadow map file was not created!"
    assert "def mock_func(): pass" in ast_file.read_text(encoding="utf-8")
