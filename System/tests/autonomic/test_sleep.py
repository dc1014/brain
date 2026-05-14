import json


def test_biological_sleep_cycle(monkeypatch, tmp_path):
    """Proves that sleep creates backups, extracts XML summaries, and stages Neuroplasticity safely."""
    from System.cli import sleep

    # 1. Setup Mock File System cleanly
    root = tmp_path
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

    # Setup dummy agents.yaml
    agents_file = config_dir / "agents.yaml"
    agents_file.write_text(
        "agents:\n  dispatcher:\n    system_prompt: 'Basic prompt.'\n", encoding="utf-8"
    )

    personal_dir = root / "Personal"
    personal_dir.mkdir()
    personal_mem = personal_dir / "personal-memory.md"
    personal_mem.write_text("<working_memory>\n- I like Java\n</working_memory>")

    # 2. Mock the LLM to return summary, neuroplasticity tag, AND usage stats
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
                                    "content": '<sleep_summary>Pruned Java, added Python.</sleep_summary>\n<neuroplasticity agent="dispatcher">Always route Python tasks to FORGE.</neuroplasticity>\n<working_memory>\n- [2026-05-08] Superseded: I like Java (Now prefers Python)\n</working_memory>'
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

    # 4. Assertions
    assert not log_file.exists(), "Hippocampus JSONL was not rotated!"
    assert list((root / "logs" / "archive").glob("hippocampus_*.jsonl")), (
        "Archive missing!"
    )

    final_memory = personal_mem.read_text()
    assert "Superseded:" in final_memory, "LLM output was not written to neocortex!"
    assert "<sleep_summary>" not in final_memory, "Summary XML leaked into vault!"

    # --- PROVE THE AIR-GAP (Guided Evolution) ---
    mutations_file = root / "Meta" / "Mutations.md"
    assert mutations_file.exists(), (
        "The OS failed to stage mutations in the Meta domain!"
    )
    assert "Always route Python tasks" in mutations_file.read_text(), (
        "The learned rule was not staged!"
    )

    agents_yaml = agents_file.read_text(encoding="utf-8")
    assert "<neuroplastic_rule" not in agents_yaml, (
        "SECURITY BREACH: Sleep command bypassed the air-gap!"
    )
    assert "<neuroplasticity" not in final_memory, (
        "The neuroplasticity XML leaked into the vault!"
    )
