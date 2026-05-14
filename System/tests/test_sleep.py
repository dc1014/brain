import json


def test_biological_sleep_cycle(monkeypatch, tmp_path):
    """Proves that sleep creates backups, prunes JSONL, rotates logs (Amnesia), and extracts XML summaries."""
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
        json.dumps(
            {"user_prompt": "I love Python", "response": "Noted.", "domain": "PERSONAL"}
        )
        + "\n"
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

    # 2. Mock the LLM to return the new XML summary AND usage stats
    monkeypatch.setattr(
        "System.cli.completion",
        lambda *args, **kwargs: type(
            "Mock",
            (),
            {
                "usage": type("MockUsage", (), {"total_tokens": 150})(),
                "choices": [
                    type(
                        "MockChoice",
                        (),
                        {
                            "message": type(
                                "MockMsg",
                                (),
                                {
                                    "content": "<sleep_summary>Pruned Java, added Python.</sleep_summary>\n<working_memory>\n- [2026-05-08] Superseded: I like Java (Now prefers Python)\n</working_memory>"
                                },
                            )()
                        },
                    )
                ],
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

    # C. Neocortex Updated and Summary Stripped?
    final_memory = personal_mem.read_text()
    assert "Superseded:" in final_memory, "LLM output was not written to neocortex!"
    assert "<sleep_summary>" not in final_memory, (
        "The UI summary XML leaked into the permanent markdown vault!"
    )
