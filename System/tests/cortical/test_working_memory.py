import pytest
from System.neuroanatomy.cortical.working_memory import WorkingMemory


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
    assert "<raw_telemetry>\nGenerated configuration\n</raw_telemetry>" in context
    assert "<actions_taken>['touch config.json']</actions_taken>" in context


@pytest.mark.asyncio
async def test_compress_if_bloated_under_threshold(mocker):
    """Verify compression is skipped if below character count threshold."""
    memory = WorkingMemory("Objective")

    # ⚡ THE FIX: Scale the threshold to 1000 so the 139-character XML node is safely below it
    memory.compression_threshold_chars = 1000
    memory.add_event("Agent", "Short telemetry", [])

    mock_acompletion = mocker.patch(
        "System.neuroanatomy.cortical.working_memory.acompletion"
    )
    await memory.compress_if_bloated()

    mock_acompletion.assert_not_called()  # ✅ Skipped cleanly, passes verification
    assert len(memory.recent_activity) == 1


@pytest.mark.asyncio
async def test_compress_if_bloated_over_threshold_success(mocker):
    """Verify compression reduces recent activity to established facts on success."""
    memory = WorkingMemory("Objective")
    memory.compression_threshold_chars = 10
    memory.add_event("Agent", "Very long telemetry output...", [])

    mock_response = mocker.AsyncMock()
    mock_response.choices[0].message.content = "Synthesized fact list"

    mocker.patch(
        "System.neuroanatomy.cortical.working_memory.acompletion",
        return_value=mock_response,
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_api_key_for_model",
        return_value="sk-fake-key",
    )

    await memory.compress_if_bloated()

    assert len(memory.recent_activity) == 0
    assert "Synthesized fact list" in memory.established_facts


@pytest.mark.asyncio
async def test_compress_if_bloated_api_failure_graceful(mocker):
    """Verify that an API exception during compression doesn't crash the pipeline."""
    memory = WorkingMemory("Objective")
    memory.compression_threshold_chars = 10
    memory.add_event("Agent", "Very long telemetry output...", [])

    mocker.patch(
        "System.neuroanatomy.cortical.working_memory.acompletion",
        side_effect=Exception("API limit hit"),
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_api_key_for_model",
        return_value="sk-fake-key",
    )

    # Telemetry execution should continue gracefully instead of blowing up the parent chain
    await memory.compress_if_bloated()

    assert len(memory.recent_activity) == 1
    assert len(memory.established_facts) == 0
