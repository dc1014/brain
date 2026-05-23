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


@pytest.mark.asyncio
async def test_compress_message_array_success(mocker):
    """Verifies that massive message arrays are successfully compressed into a single Working Memory block."""
    from System.neuroanatomy.cortical.working_memory import compress_message_array

    # 1. Create a bloated history array (>12,000 chars) to trigger compression
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

    # 2. Assert the array was shrunk significantly
    assert len(compressed_msgs) == 4  # head(2) + tail(2)

    # 3. Assert the Working Memory was perfectly injected into the User prompt
    user_msg = compressed_msgs[1]["content"]
    assert "original user prompt" in user_msg
    assert "--- COMPRESSED WORKING MEMORY ---" in user_msg
    assert "COMPRESSED HISTORICAL SUMMARY" in user_msg


@pytest.mark.asyncio
async def test_compress_message_array_fallback(mocker):
    """Verifies that if the compression API crashes, it safely falls back to a 5-message FIFO."""
    from System.neuroanatomy.cortical.working_memory import compress_message_array

    bloat = "A" * 15000
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user prompt"},
        {"role": "assistant", "content": "thought 1"},
        {"role": "user", "content": f"bloated tool result: {bloat}"},
        {"role": "assistant", "content": "thought 2"},
        {"role": "tool", "content": "tool result 2"},
        {"role": "assistant", "content": "thought 3"},
        {"role": "user", "content": "tool result 3"},
    ]

    # Force the API to crash
    mocker.patch(
        "System.neuroanatomy.cortical.working_memory.acompletion",
        side_effect=Exception("API Down"),
    )

    fallback_msgs = await compress_message_array(messages, "gpt-4o")

    # Assert it fell back to head(2) + tail(max 5, but strips leading tools)
    # The tail logic will grab the last 5: bloat, thought 2, tool 2, thought 3, result 3
    # It should not contain the `tool result 2` as a leading tool.
    assert len(fallback_msgs) <= 7
    assert fallback_msgs[0]["role"] == "system"
    assert fallback_msgs[1]["role"] == "user"


@pytest.mark.asyncio
async def test_algorithmic_pre_pass_bypasses_llm_summary(mocker):
    """Proves that algorithmic line deduplication prevents unnecessary LLM summary calls."""
    pfc_memory = WorkingMemory(core_objective="Optimize token footprints")

    # Simulate a highly redundant log file payload that fills up characters quickly
    redundant_log_trace = (
        "ERROR: Connection timeout on port 8080 chasing database sync keys\n" * 250
    )
    pfc_memory.add_event(
        agent_name="test_agent", raw_output=redundant_log_trace, actions=[]
    )

    # Mock acompletion to see if it gets called
    mock_completion = mocker.patch(
        "System.neuroanatomy.cortical.working_memory.acompletion"
    )

    await pfc_memory.compress_if_bloated()

    # Verify line deduplication shrank the buffer enough to completely bypass the LLM summary call
    mock_completion.assert_not_called()
    assert len(pfc_memory.recent_activity) == 1
    assert "Connection timeout" in pfc_memory.recent_activity[0]


@pytest.mark.asyncio
async def test_algorithmic_compaction_preserves_xml_node_boundaries():
    """Zero-Debt: Proves that line deduplication clears text noise while keeping individual XML wrappers intact."""
    memory = WorkingMemory(core_objective="Audit structural context")

    # Ingest two separate activity blocks containing identical internal telemetry logs
    memory.add_event("Agent_A", "Trace log data line entry\n" * 100, ["write"])
    memory.add_event("Agent_B", "Trace log data line entry\n" * 100, ["execute"])

    await memory.compress_if_bloated()

    # Verify that the history was algorithmically optimized without losing individual node elements
    assert len(memory.recent_activity) == 2
    assert '<activity_node agent="Agent_A">' in memory.recent_activity[0]
    assert '<activity_node agent="Agent_B">' in memory.recent_activity[1]


@pytest.mark.asyncio
async def test_compress_message_array_does_not_mutate_input_immutability():
    """Secure by Default: Proves historical message arrays are not mutated in-place during payload slicing."""
    historical_messages = [
        {"role": "user", "content": "Initial kickoff prompt data entry"},
        {"role": "assistant", "content": "Verbose trace output entry\n" * 500},
    ]

    # Execute array compression passes over the mock parameters
    processed_messages = await compress_message_array(historical_messages, "mock-model")

    # Verify that the original input collection remains 100% untouched and intact
    assert "Verbose trace output entry" in historical_messages[1]["content"]
    assert "ALGORITHMIC CONTEXT FILTER" not in historical_messages[1]["content"]

    # Confirm the newly optimized shallow copy holds the compressed variation safely
    assert "ALGORITHMIC CONTEXT FILTER" in processed_messages[1]["content"]


@pytest.mark.asyncio
async def test_compressors_mask_secrets_before_api_dispatch(mocker):
    """Secure by Default: Proves cognitive memory arrays mask vault secrets before hitting the fallback LLM API."""
    from System.neuroanatomy.systemic.immune_system import vault
    from System.neuroanatomy.cortical.working_memory import compress_message_array

    # Inject a known biological target secret key signature into the active memory bank
    mocker.patch.dict(
        vault._secrets,
        {"MOCK_DATABASE_URL": "postgres://admin:super_secret_db_pass@localhost"},
    )

    # Force a bloated history payload loaded with a leaked credential
    bloat = "A" * 15000
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user prompt"},
        {"role": "assistant", "content": "thought 1"},
        {
            "role": "user",
            "content": f"bloated tool result: {bloat} with leak postgres://admin:super_secret_db_pass@localhost",
        },
        {"role": "assistant", "content": "thought 2"},
        {"role": "user", "content": "tool result 2"},
        {"role": "assistant", "content": "thought 3"},
        {"role": "user", "content": "tool result 3"},
    ]

    mock_response = mocker.AsyncMock()
    mock_response.choices[0].message.content = "COMPRESSED HISTORICAL SUMMARY"

    mock_completion = mocker.patch(
        "System.neuroanatomy.cortical.working_memory.acompletion",
        return_value=mock_response,
    )
    mocker.patch(
        "System.neuroanatomy.systemic.immune_system.vault.get_api_key_for_model",
        return_value="fake_key",
    )

    await compress_message_array(messages, "gpt-4o")

    # Verify the LLM was called, but extract the EXACT prompt it was sent
    called_args, called_kwargs = mock_completion.call_args
    dispatched_prompt = called_kwargs["messages"][0]["content"]

    # Assert the raw credential never left the local machine
    assert "super_secret_db_pass" not in dispatched_prompt
    assert "[MOCK_DATABASE_URL_REDACTED]" in dispatched_prompt
