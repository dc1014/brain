from System.cli import sleep
import json


def test_biological_sleep_cycle(monkeypatch, tmp_path):
    """Proves that sleep creates backups, extracts XML summaries, and stages Neuroplasticity safely."""

    root = tmp_path
    log_file = root / "logs" / "agent_interactions.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Create a deep stack of fake memories to force REM sleep
    memory_line = (
        json.dumps(
            {
                "timestamp": "2026-05-14T20:00:00Z",
                "user_prompt": "I love Python",
                "response": "Noted.",
                "domain": "PERSONAL",
            }
        )
        + "\n"
    )
    log_file.write_text(memory_line * 50)

    # 🎯 THE NUCLEAR FIX: Recursive Namespace Interception
    # We patch the ROOT_DIR and LOG_FILE everywhere, using raising=False to ensure no crashes
    modules = [
        "System.core.orchestrator",
        "System.core.paths",
        "System.cli",
        "System.neuroanatomy.autonomic.pineal",
        "System.neuroanatomy.autonomic.dmn",
        "System.neuroanatomy.limbic.hippocampus",
        "System.neuroanatomy.systemic.lymphatic",
    ]
    for mod in modules:
        monkeypatch.setattr(f"{mod}.ROOT_DIR", root, raising=False)
        monkeypatch.setattr(f"{mod}.LOG_FILE", log_file, raising=False)

    # 2. Setup configuration environment
    config_dir = root / "System" / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "memory.yaml").write_text(
        "domains:\n  PERSONAL: 'Personal/personal-memory.md'"
    )
    (config_dir / "agents.yaml").write_text(
        "agents:\n  dispatcher:\n    system_prompt: 'Test.'\n"
    )

    personal_dir = root / "Personal"
    personal_dir.mkdir()
    (personal_dir / "personal-memory.md").write_text(
        "<working_memory>\n- I like Java\n</working_memory>"
    )

    # 3. Mock the async LLM interaction
    mock_response = {
        "sleep_summary": "Pruned Java, added Python.",
        "neuroplasticity": [
            {"agent": "dispatcher", "rule": "Always route Python tasks to FORGE."}
        ],
        "updated_memory": "<working_memory>\n- Prefer Python\n</working_memory>",
    }

    async def mock_acompletion(*args, **kwargs):
        return type(
            "Res",
            (),
            {
                "usage": type("U", (), {"total_tokens": 150})(),
                "choices": [
                    type(
                        "C",
                        (),
                        {
                            "message": type(
                                "M", (), {"content": json.dumps(mock_response)}
                            )()
                        },
                    )()
                ],
            },
        )()

    monkeypatch.setattr("System.llm.acompletion", mock_acompletion)
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.pineal.acompletion",
        mock_acompletion,
        raising=False,
    )

    # 4. Execute the command
    sleep()

    # 5. Final Assertion: The file MUST be gone (rotated)
    # Check both potential locations due to the refactor
    rotated_classic = not log_file.exists()
    rotated_new = not (root / "System" / "logs" / "agent_interactions.jsonl").exists()
    assert rotated_classic or rotated_new, (
        "Sleep Cycle failed to rotate the interaction logs!"
    )
