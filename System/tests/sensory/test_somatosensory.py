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


def test_transducer_strips_ansi_and_noise():
    from System.neuroanatomy.sensory.somatosensory import SensoryTransducer

    transducer = SensoryTransducer()

    # Separated standalone ephemeral spinner frames into their own independent lines
    noisy_input = "\x1b[31mError: check failed\x1b[0m\n⠋ Loading packages...\nDownloaded 42 packages looking for funding"
    compacted = transducer.compact_terminal_output(["pytest"], noisy_input)

    assert "Error:" in compacted
    assert "Loading" not in compacted
    assert "funding" not in compacted


def test_transducer_safe_inventory_bypass():
    from System.neuroanatomy.sensory.somatosensory import SensoryTransducer

    transducer = SensoryTransducer()

    code_payload = "import os\nprint(os.getenv('PATH'))"
    compacted = transducer.compact_terminal_output(["cat", "safe.py"], code_payload)

    # Safe-inventory check means data code reads remain completely raw and pristine
    assert compacted == code_payload


def test_transducer_head_tail_slicing():
    from System.neuroanatomy.sensory.somatosensory import SensoryTransducer

    transducer = SensoryTransducer(max_lines=10, head_slice=2, tail_slice=2)

    long_log = "\n".join(f"Line item {i}" for i in range(100))
    compacted = transducer.compact_terminal_output(["pytest"], long_log)

    assert "Line item 0" in compacted
    assert "Line item 1" in compacted
    assert "SENSORY COMPACTOR: Truncated" in compacted
    assert "Line item 98" in compacted
    assert "Line item 99" in compacted


def test_transducer_masks_vault_secrets_before_truncation(mocker):
    """Secure by Default: Proves credentials are masked cleanly before head/tail slicing executes."""
    from System.neuroanatomy.sensory.somatosensory import SensoryTransducer
    from System.neuroanatomy.systemic.immune_system import vault

    # Inject a known biological target secret key signature into the active memory bank
    mocker.patch.dict(
        vault._secrets, {"MOCK_DEPLOYMENT_TOKEN": "super_secret_token_string_xyz_12345"}
    )

    # Enforce strict low margins to test interception around a truncation boundary line drop
    transducer = SensoryTransducer(max_lines=4, head_slice=1, tail_slice=1)

    leaked_output = (
        "Deployment initiating...\n"
        "Active session token value: super_secret_token_string_xyz_12345\n"
        "Connecting to clusters...\n"
        "Process complete."
    )

    compacted = transducer.compact_terminal_output(["pytest"], leaked_output)

    # Confirm plaintext credential signatures are completely non-existent
    assert "super_secret_token_string_xyz_12345" not in compacted
    assert "[MOCK_DEPLOYMENT_TOKEN_REDACTED]" in compacted
