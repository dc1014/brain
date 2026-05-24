# --- System/tests/cortical/test_working_memory.py ---
import pytest
from System.neuroanatomy.cortical.working_memory import (
    WorkingMemory,
    compress_message_array,
)


def test_working_memory_init():
    """Verify core objective initialization and empty state."""
    memory = WorkingMemory("Build a compiler")
    assert memory.core_objective == "Build a compiler"
    assert memory.established_facts == []
    assert memory.recent_activity == []


def test_working_memory_add_event_xml_structure():
    """Verify that events are successfully wrapped in strict, clean XML blocks."""
    memory = WorkingMemory("Deploy application")
    memory.add_event("PM", "Generated configuration", ["touch config.json"])
    context = memory.get_current_context()
    assert "CORE OBJECTIVE: Deploy application" in context
    assert '<activity_node agent="PM">' in context


def test_prune_and_get_overflow_under_threshold():
    """Verify that short events do not trigger text overflow requests."""
    memory = WorkingMemory("Objective")
    memory.compression_threshold_chars = 1000
    memory.add_event("Agent", "Short telemetry", [])
    overflow = memory.prune_and_get_overflow()
    assert overflow is None


def test_prune_and_get_overflow_and_summary_ingestion():
    """Verify overflow boundary detection and downstream summary ingestion."""
    memory = WorkingMemory("Objective")
    memory.compression_threshold_chars = 10
    memory.add_event("Agent", "Very long telemetry output...", [])

    # 1. Verify data structure properly yields overflow string for service layers
    overflow = memory.prune_and_get_overflow()
    assert overflow is not None
    assert "Very long telemetry output..." in overflow

    # 2. Verify state tracking updates cleanly upon summary integration
    memory.add_summary("Synthesized fact list")
    assert "Synthesized fact list" in memory.established_facts
    assert len(memory.recent_activity) == 0


@pytest.mark.asyncio
async def test_compress_message_array_success(mocker):
    bloat = "A" * 15000
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "original user prompt"},
        {"role": "assistant", "content": "thought 1"},
        {"role": "user", "content": f"bloated tool result: {bloat}"},
        {"role": "assistant", "content": "thought 2"},
        {"role": "user", "content": "tool result 2"},
        {"role": "assistant", "content": "thought 3 (tail)"},
        {"role": "user", "content": "tool result 3 (tail)"},
    ]
    mock_response = mocker.AsyncMock()
    mock_response.choices[0].message.content = "COMPRESSED HISTORICAL SUMMARY"
    mocker.patch(
        "System.neuroanatomy.cortical.working_memory.acompletion",
        return_value=mock_response,
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_api_key_for_model",
        return_value="fake_key",
    )
    compressed_msgs = await compress_message_array(messages, "gpt-4o")
    assert len(compressed_msgs) == 4


def test_working_memory_pipeline_persistence(tmp_path, monkeypatch):
    """Proves Working Memory can save and clear the active execution queue safely."""
    import json
    from System.neuroanatomy.cortical.working_memory import (
        persist_pipeline_state,
        clear_pipeline_state,
    )

    mock_queue_file = tmp_path / "execution_queue.json"
    monkeypatch.setattr(
        "System.neuroanatomy.cortical.working_memory.QUEUE_FILE_PATH", mock_queue_file
    )

    fake_pipeline = [{"agent": "frontend_engineer"}, {"agent": "qa_auditor"}]
    persist_pipeline_state("Build a button", "FORGE", "STUDIO", fake_pipeline)

    assert mock_queue_file.exists()
    with open(mock_queue_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["original_task"] == "Build a button"
    clear_pipeline_state()
    assert not mock_queue_file.exists()
