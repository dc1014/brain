import pytest
from System.neuroanatomy.cortical.motor_cortex import execute_tools


@pytest.mark.asyncio
async def test_motor_cortex_forgives_nested_parameters_and_filepath_typos(mocker):
    """
    UNIT: Proves the MotorCortex intercepts LLM schema hallucinations
    (nested 'parameters' blocks and 'file_path' instead of 'filepath')
    and normalizes them to prevent tool crashes.
    """

    # 1. Simulate the exact Daydreamer LLM hallucination
    hallucinated_args = {
        "parameters": {
            "file_path": "Meta/DMN/daydreams.md",
            "content": "## Epiphany\nSystem optimized.",
        }
    }

    mock_tool_call = {
        "tool_name": "append_safe_file",
        "parameters": hallucinated_args,
        "id": "call_dmn_123",
    }

    # 2. Spy on the actual underlying file system tool to see what arguments it receives
    mock_append = mocker.patch("System.tools.append_safe_file")

    # 3. Execute the hallucinated payload through the Motor Cortex
    messages, actions, halt_text = await execute_tools(
        [mock_tool_call], role_name="The Daydreamer"
    )

    # 4. Verify the tool was executed and the arguments were perfectly flattened/normalized
    mock_append.assert_called_once()
    called_kwargs = mock_append.call_args.kwargs

    assert "filepath" in called_kwargs, (
        "MotorCortex failed to map 'file_path' to 'filepath'"
    )
    assert called_kwargs["filepath"] == "Meta/DMN/daydreams.md"
    assert called_kwargs["content"] == "## Epiphany\nSystem optimized."
    assert "parameters" not in called_kwargs, (
        "MotorCortex failed to flatten the nested 'parameters' block"
    )

    assert "[APPEND_SAFE_FILE] Executed" in actions[0]
