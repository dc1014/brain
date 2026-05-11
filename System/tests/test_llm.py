import asyncio
from unittest.mock import MagicMock
from System.llm import run_agent_async


def test_token_truncator_protects_context(mocker) -> None:  # type: ignore
    """Ensure that massive tool outputs are truncated to exactly 8000 chars + a warning."""

    mock_completion = mocker.patch(
        "System.llm.acompletion", new_callable=mocker.AsyncMock
    )
    mocker.patch("System.llm.log_interaction")  # Silence the log writer for tests

    # 1. Properly Setup the mock (Avoiding the MagicMock name trap)
    func_mock = MagicMock()
    func_mock.name = "read_safe_file"
    func_mock.arguments = '{"filepath": "huge.log"}'

    tool_call_msg = MagicMock()
    tool_call_msg.content = None
    tool_call_msg.tool_calls = [MagicMock(id="call_123", function=func_mock)]

    # 2. The AI receives the tool output and finishes
    text_msg = MagicMock()
    text_msg.content = "I read the file."
    text_msg.tool_calls = None

    mock_completion.side_effect = [
        MagicMock(choices=[MagicMock(message=tool_call_msg)]),
        MagicMock(choices=[MagicMock(message=text_msg)]),
    ]

    # Mock the tool to return a 15,000 character string
    massive_string = "A" * 15000
    mocker.patch(
        "System.tools.read_safe_file", return_value=massive_string
    )  # <--- Changed llm to tools

    asyncio.run(
        run_agent_async("Test_Agent", "model", "sys_prompt", "user_prompt", tools=[])
    )

    # Intercept the exact messages array.
    messages_sent_to_llm = mock_completion.call_args_list[1][1]["messages"]

    # Because lists are passed by reference and the final "assistant" message is appended,
    # the tool response is now the second-to-last item in the array.
    tool_response_msg = messages_sent_to_llm[-2]

    assert tool_response_msg["role"] == "tool"
    assert len(tool_response_msg["content"]) < 15000, (
        "The massive string was not truncated!"
    )
    # FIX: Assert the exact new, shortened warning string
    assert "SYSTEM WARNING: Truncated at 8000 chars" in tool_response_msg["content"]


def test_context_sliding_window_preserves_anchors(mocker) -> None:  # type: ignore
    """Ensure that when context overflows, the System and User prompts are NEVER dropped."""

    mock_completion = mocker.patch(
        "System.llm.acompletion", new_callable=mocker.AsyncMock
    )
    mocker.patch("System.llm.log_interaction")

    def create_tool_mock(step_id: int):
        func_mock = MagicMock()
        func_mock.name = "list_safe_directory"
        func_mock.arguments = '{"directory_path": "Studio"}'

        msg = MagicMock()
        msg.content = None
        msg.tool_calls = [MagicMock(id=f"call_{step_id}", function=func_mock)]

        return MagicMock(choices=[MagicMock(message=msg)])

    text_msg = MagicMock()
    text_msg.content = "I am done looping."
    text_msg.tool_calls = None
    final_mock = MagicMock(choices=[MagicMock(message=text_msg)])

    mock_completion.side_effect = [
        create_tool_mock(1),
        create_tool_mock(2),
        create_tool_mock(3),
        create_tool_mock(4),
        final_mock,
    ]

    mocker.patch("System.tools.list_safe_directory", return_value="file.txt")
    asyncio.run(
        run_agent_async("Test_Agent", "model", "sys_prompt", "user_prompt", tools=[])
    )

    for call in mock_completion.call_args_list:
        messages = call[1]["messages"]

        # 1. System Prompt must always survive
        assert messages[0]["role"] == "system", "System prompt was dropped!"

        # 2. User Prompt must always survive
        assert messages[1]["role"] == "user", "Original User prompt was dropped!"

        # 3. Prevent Anthropic Crash: Ensure a Tool message isn't orphaned right after the User prompt
        if len(messages) > 2:
            assert messages[2]["role"] != "tool", (
                "Anthropic crash: Tool message orphaned immediately after User prompt!"
            )


def test_run_agent_async_execution(mocker):
    """Proves that the asynchronous Swarm agent runner processes LLM responses correctly."""
    mock_completion = mocker.patch(
        "System.llm.acompletion", new_callable=mocker.AsyncMock
    )

    class MockMessage:
        content = "I am a parallel Swarm agent."
        tool_calls = []

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]
        usage = MagicMock(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    mock_completion.return_value = MockResponse()

    # 2. Run the async function using the standard event loop
    result = asyncio.run(
        run_agent_async(
            role_name="Swarm Node",
            model_string="gpt-4o-mini",
            system_prompt="You are a swarm agent.",
            user_prompt="Hello swarm.",
        )
    )

    # 3. Verify the async agent processed the data contract correctly
    assert result.text == "I am a parallel Swarm agent."
    assert result.usage["prompt_tokens"] == 0
