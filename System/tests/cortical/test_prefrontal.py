import pytest
from System.neuroanatomy.cortical.prefrontal import PrefrontalCortex, WorkingMemory

# --- 1. NEW COMPRESSOR TESTS ---


def test_pfc_working_memory_accumulation():
    """Proves the PFC accurately tracks and formats established facts and recent activity."""
    memory = WorkingMemory("Build a web server")
    memory.add_event("Architect", "Created the folder structure", ["mkdir src"])

    context = memory.get_current_context()
    assert "CORE OBJECTIVE: Build a web server" in context
    assert "Architect Output" in context
    assert "mkdir src" in context


@pytest.mark.asyncio
async def test_pfc_working_memory_compression(mocker):
    """Proves the PFC autonomically compresses activity when the token threshold is exceeded."""
    memory = WorkingMemory("Build a web server")

    # Artificially lower the compression threshold for testing
    memory.compression_threshold_chars = 100

    # Bloat the memory
    memory.add_event(
        "Coder", "This is a very long log output full of redundant data " * 5, []
    )

    # Mock the LLM summary
    mock_response = mocker.AsyncMock()
    mock_response.choices[0].message.content = "Compressed Fact: Web server scaffolded."
    mocker.patch(
        "System.neuroanatomy.cortical.prefrontal.acompletion",
        return_value=mock_response,
    )

    await memory.compress_if_bloated()

    # Verify the heavy logs were flushed and the compressed fact was retained
    assert len(memory.recent_activity) == 0
    assert len(memory.established_facts) == 1
    assert "Compressed Fact" in memory.established_facts[0]


# --- 2. RESTORED LEGACY TESTS ---


def test_pfc_working_memory_legacy():
    """Proves the old PFC rolling working memory respects maximum limits."""
    pfc = PrefrontalCortex()
    pfc.max_memory = 2

    pfc._remember("Task 1")
    pfc._remember("Task 2")
    pfc._remember("Task 3")

    assert len(pfc.working_memory) == 2
    assert pfc.working_memory == ["Task 2", "Task 3"]
    assert "Task 2" in pfc.get_working_memory_context()


def test_pfc_decompose_fallback(mocker):
    """Proves the PFC safely catches API errors and passes the raw objective."""
    mocker.patch(
        "System.neuroanatomy.cortical.prefrontal.completion",
        side_effect=Exception("API Down"),
    )

    pfc = PrefrontalCortex()
    tasks = pfc.decompose_goal("Do everything")

    assert len(tasks) == 1
    assert tasks[0] == "Do everything"


def test_pfc_decompose_success(mocker):
    """Proves the PFC successfully parses JSON arrays from the LLM."""

    class MockMessage:
        content = '["Step 1", "Step 2"]'

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    mocker.patch(
        "System.neuroanatomy.cortical.prefrontal.completion",
        return_value=MockResponse(),
    )

    pfc = PrefrontalCortex()
    tasks = pfc.decompose_goal("Do everything")

    assert len(tasks) == 2
    assert tasks[0] == "Step 1"


@pytest.mark.asyncio
async def test_pfc_execute_goal(mocker):
    """Proves the PFC orchestrates multiple pulses and updates memory accordingly."""
    pfc = PrefrontalCortex()
    mocker.patch.object(pfc, "decompose_goal", return_value=["Task A", "Task B"])
    mocker.patch(
        "System.neuroanatomy.cortical.prefrontal.recall_recent_episodes",
        return_value="No history.",
    )
    mocker.patch("System.neuroanatomy.cortical.prefrontal.encode_episode")
    mock_dispatch = mocker.AsyncMock()
    mocker.patch("System.core.orchestrator.dispatch_task", mock_dispatch)

    await pfc.execute_goal("Complete all tasks", "STUDIO")

    assert mock_dispatch.call_count == 2
    assert "Task A" in mock_dispatch.call_args_list[0][0][0]
    assert "Task B" in mock_dispatch.call_args_list[1][0][0]
