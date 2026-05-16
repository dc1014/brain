import pytest
from System.neuroanatomy.cortical.prefrontal import PrefrontalCortex


def test_pfc_working_memory():
    """Proves the PFC rolling working memory respects maximum limits."""
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
    from System.neuroanatomy.cortical.prefrontal import PrefrontalCortex

    pfc = PrefrontalCortex()

    # Mock decomposition into 2 pulses
    mocker.patch.object(pfc, "decompose_goal", return_value=["Task A", "Task B"])

    # Mock Episodic Memory to isolate the test
    mocker.patch(
        "System.neuroanatomy.cortical.prefrontal.recall_recent_episodes",
        return_value="No history.",
    )
    mock_encode = mocker.patch("System.neuroanatomy.cortical.prefrontal.encode_episode")

    # Mock the dispatcher to avoid actual execution
    mock_dispatch = mocker.AsyncMock()
    mocker.patch("System.core.orchestrator.dispatch_task", mock_dispatch)

    await pfc.execute_goal("Goal", "STUDIO", "FORGE")

    assert mock_dispatch.call_count == 2
    assert "Task A" in pfc.working_memory[0]
    assert "Task B" in pfc.working_memory[1]
    mock_encode.assert_called_once_with("Goal", ["Task A", "Task B"], "Success")
