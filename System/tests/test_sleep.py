import json


def test_biological_sleep_cycle(monkeypatch, tmp_path):
    """Proves that sleep creates backups, prunes JSONL, and rotates logs (Amnesia)."""
    from System.cli import sleep

    # 1. Setup Mock File System cleanly
    root = tmp_path
    # SHIFT-LEFT: Mock the global variable, not the Path object
    monkeypatch.setattr("System.cli.ROOT_DIR", root)

    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "agent_interactions.jsonl"

    # Write mock hippocampus data
    log_file.write_text(
        json.dumps({"user_prompt": "I love Python", "response": "Noted."}) + "\n"
    )

    # Setup config and neocortex
    config_dir = root / "System" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "memory.yaml").write_text(
        "domains:\n  PERSONAL: 'Personal/personal-memory.md'"
    )

    personal_dir = root / "Personal"
    personal_dir.mkdir()
    personal_mem = personal_dir / "personal-memory.md"
    personal_mem.write_text("<working_memory>\n- I like Java\n</working_memory>")

    # 2. Mock the LLM to return a "pruned" string
    monkeypatch.setattr(
        "System.cli.completion",
        lambda *args, **kwargs: type(
            "Mock",
            (),
            {
                "choices": [
                    type(
                        "MockChoice",
                        (),
                        {
                            "message": type(
                                "MockMsg",
                                (),
                                {
                                    "content": "<working_memory>\n- Superseded: I like Java (Now prefers Python)\n</working_memory>"
                                },
                            )()
                        },
                    )
                ]
            },
        )(),
    )

    # 3. Execute
    sleep()

    # 4. Assertions (Shift-Left Validation)
    # A. Amnesia worked?
    assert not log_file.exists(), "Hippocampus JSONL was not rotated!"
    assert list((root / "logs" / "archive").glob("hippocampus_*.jsonl")), (
        "Archive file missing!"
    )

    # B. Immutable Backup created?
    assert list((root / "logs" / "backups").glob("personal-memory_*.md")), (
        "Memory backup missing!"
    )

    # C. Neocortex Updated?
    assert "Superseded:" in personal_mem.read_text(), (
        "LLM output was not written to neocortex!"
    )
