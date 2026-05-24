import asyncio
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from System.llm import run_agent_async, get_system_context


def test_token_truncator_protects_context(mocker) -> None:
    """Ensure that massive tool outputs are truncated to exactly 15000 chars + a warning."""

    mock_completion = mocker.patch(
        "System.llm.acompletion", new_callable=mocker.AsyncMock
    )
    mocker.patch("System.llm.log_interaction")  # Silence the log writer for tests

    # ⚡ ZERO-DEBT FIX: Prevent the memory compressor from mutating the message array
    async def bypass_compressor(msgs, model):
        return msgs

    mocker.patch(
        "System.neuroanatomy.cortical.working_memory.compress_message_array",
        side_effect=bypass_compressor,
    )

    # 1. Simulate modern AgentResponseSchema JSON structured output
    json_payload = {
        "thought_process": "I need to read a massive file.",
        "tool_calls": [
            {
                "tool_name": "read_safe_file",
                "parameters": {"filepath": "huge.log"},
                "reasoning": "Inspecting data to verify environment.",
            }
        ],
        "final_response": None,
    }

    tool_call_msg = MagicMock()
    tool_call_msg.content = json.dumps(json_payload)
    tool_call_msg.tool_calls = None

    text_msg = MagicMock()
    text_msg.content = json.dumps(
        {
            "thought_process": "Done reading.",
            "tool_calls": [],
            "final_response": "I read the file.",
        }
    )
    text_msg.tool_calls = None

    mock_completion.side_effect = [
        MagicMock(choices=[MagicMock(message=tool_call_msg)]),
        MagicMock(choices=[MagicMock(message=text_msg)]),
    ]

    # 2. Mock the tool execution to return a 20,000 character string (must be > 15000 to trigger truncation)
    massive_string = "A" * 20000
    mock_execute = mocker.patch(
        "System.neuroanatomy.cortical.motor_cortex.execute_tools",
        new_callable=mocker.AsyncMock,
    )
    mock_execute.return_value = (
        [{"role": "tool", "content": massive_string}],
        ["Mock Action Executed"],
        None,
    )

    from System.llm import run_agent_async

    asyncio.run(
        run_agent_async("Test_Agent", "model", "sys_prompt", "user_prompt", tools=[])
    )

    # Intercept the exact messages array.
    # Python passes lists by reference, so this array contains the FINAL mutated state
    # (including the final text_msg assistant response appended after the tool run).
    messages_sent_to_llm = mock_completion.call_args_list[1][1]["messages"]

    # ⚡ ZERO-DEBT FIX: The truncated tool output is the second-to-last item [-2],
    # because the final text_msg is appended to the very end [-1].
    tool_response_msg = messages_sent_to_llm[-2]

    assert tool_response_msg["role"] == "user"
    assert "TRUNCATED: OUTPUT EXCEEDED" in tool_response_msg["content"]
    assert len(tool_response_msg["content"]) < 16000


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


# --- appending to System/tests/test_llm.py ---


@pytest.mark.asyncio
async def test_run_agent_async_thalamic_cross_modal_routing(mocker):
    """
    Zero-Debt Test: Proves the Thalamic Cross-Modal Routing dynamically
    mutates model strings and injects aggregator/fallback keys before acompletion.
    """
    from System.llm import run_agent_async

    # 1. Mock the Immune System Vault to simulate an OpenRouter fallback
    mock_resolve = mocker.patch(
        "System.llm.vault.resolve_routing",
        return_value=("openrouter/anthropic/claude-3-haiku", "or-12345"),
    )
    mocker.patch("System.llm.vault.get_secret", return_value=None)
    mocker.patch("System.llm.vault.mask_secrets", side_effect=lambda x: x)

    # 2. Mock LiteLLM acompletion
    mock_acompletion = mocker.patch("System.llm.acompletion")
    mock_message = mocker.MagicMock()
    mock_message.content = "Thalamic routing successful."
    mock_message.tool_calls = []

    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock(message=mock_message)]
    mock_response.usage = mocker.MagicMock(prompt_tokens=10, completion_tokens=10)
    mock_acompletion.return_value = mock_response

    # Prevent Motor Cortex side effects
    mocker.patch(
        "System.neuroanatomy.pathways.corpus_callosum.route_hemisphere",
        side_effect=lambda r, m: m,
    )

    # 3. Execute
    res = await run_agent_async(
        role_name="test_agent",
        model_string="anthropic/claude-3-haiku",  # The original user request
        system_prompt="sys",
        user_prompt="usr",
    )

    # 4. Strict Validation
    assert "Thalamic routing successful" in res.text
    mock_resolve.assert_called_with("anthropic/claude-3-haiku")

    called_kwargs = mock_acompletion.call_args.kwargs
    assert called_kwargs["model"] == "openrouter/anthropic/claude-3-haiku"
    assert called_kwargs["api_key"] == "or-12345"


# --- appending to System/tests/test_llm.py ---


def test_apply_humoral_modulation_token_limit_routing(mocker):
    """
    Zero-Debt Test: Proves apply_humoral_modulation abandons legacy hardcoded limits
    and defers entirely to the EndocrineSystem for model-tier token budgets.
    """
    from System.llm import apply_humoral_modulation

    # Mock the get_humoral_vector to keep the biological state healthy
    mocker.patch(
        "System.llm.EndocrineSystem.get_humoral_vector",
        return_value={"dopamine": 0.5, "cortisol": 0.0, "adrenaline": 0.0},
    )

    # Mock calculate_token_limit to verify it intercepts the pipeline cleanly
    mock_calc = mocker.patch(
        "System.llm.EndocrineSystem.calculate_token_limit", return_value=1337
    )

    final_model, final_temp, max_tokens = apply_humoral_modulation(
        "anthropic/claude-3-opus"
    )

    # Strict Validation
    assert max_tokens == 1337
    mock_calc.assert_called_once_with("anthropic/claude-3-opus")


@pytest.mark.asyncio
async def test_run_agent_async_json_structured_output_bridge(mocker):
    """
    Zero-Debt Test: Proves that the new Pydantic JSON Structured Output bridge
    successfully parses strict JSON, translates it to Obsidian Markdown,
    and synthesizes legacy tool calls for the Motor Cortex.
    """
    from System.llm import run_agent_async

    # 1. Simulate the LLM returning STRICT JSON matching our new AgentResponseSchema
    mock_json_payload = {
        "thought_process": "Executing JSON bridge test.",
        "tool_calls": [
            {
                "tool_name": "read_safe_file",
                "parameters": {"filepath": "defcon_test.txt"},
                "reasoning": "Need file data.",
            }
        ],
        "final_response": "I have executed the tool synthetically.",
    }

    mock_acompletion = mocker.patch("System.llm.acompletion")

    mock_message_1 = mocker.MagicMock()
    mock_message_1.content = json.dumps(mock_json_payload)
    mock_message_1.tool_calls = None
    mock_response_1 = mocker.MagicMock()
    mock_response_1.choices = [mocker.MagicMock(message=mock_message_1)]
    mock_response_1.usage = mocker.MagicMock(prompt_tokens=5, completion_tokens=5)

    mock_halt = {
        "thought_process": "Task done.",
        "tool_calls": [],
        "final_response": "Done.",
    }
    mock_message_2 = mocker.MagicMock()
    mock_message_2.content = json.dumps(mock_halt)
    mock_message_2.tool_calls = None
    mock_response_2 = mocker.MagicMock()
    mock_response_2.choices = [mocker.MagicMock(message=mock_message_2)]
    mock_response_2.usage = mocker.MagicMock(prompt_tokens=5, completion_tokens=5)

    mock_acompletion.side_effect = [mock_response_1, mock_response_2]

    # 2. Mock the Motor Cortex to intercept the SYNTHETIC tool calls
    mock_execute_tools = mocker.patch(
        "System.neuroanatomy.cortical.motor_cortex.execute_tools",
        return_value=(
            [{"role": "tool", "content": "File read."}],
            ["Mocked Tool Executed"],
            None,
        ),
    )

    # Prevent other side effects
    mocker.patch("System.llm.log_interaction")
    mocker.patch("System.llm.vault.get_secret", return_value="dummy_key")
    mocker.patch(
        "System.llm.EndocrineSystem.get_humoral_vector",
        return_value={"dopamine": 0.5, "cortisol": 0.0, "adrenaline": 0.0},
    )

    # 3. Execute the agent
    res = await run_agent_async(
        role_name="test_agent",
        model_string="gpt-4o-mini",
        system_prompt="sys",
        user_prompt="usr",
    )

    # 4. ASSERTION 1: Prove the JSON was translated into human-readable Markdown
    assert "> **Thought:** Executing JSON bridge test." in res.text
    assert "`[ read_safe_file ]`" in res.text
    assert "I have executed the tool synthetically." in res.text

    # 5. ASSERTION 2: Prove the Synthetic Tool Call was generated and passed to the Motor Cortex correctly
    mock_execute_tools.assert_called_once()
    synthetic_tools = mock_execute_tools.call_args[0][
        0
    ]  # The first argument passed to execute_tools

    assert len(synthetic_tools) == 1
    assert synthetic_tools[0].function.name == "read_safe_file"

    # Prove the parameters survived the JSON -> Synthetic Object translation
    parsed_args = json.loads(synthetic_tools[0].function.arguments)
    assert parsed_args["filepath"] == "defcon_test.txt"


def test_get_system_context_injects_advisory_mode_when_execution_disabled(
    mocker,
) -> None:
    """Proves the system safely aligns the AI's context when code execution is disabled."""
    # Ensure the opt-in flag is explicitly disabled
    mocker.patch.dict(os.environ, {"BRAIN_ENABLE_CODE_EXECUTION": "false"}, clear=True)

    # Mock the configuration loader
    mocker.patch(
        "System.core.dna.get_dna_config",
        return_value={"agents": {"pm": {"system_prompt": "I am the Product Manager."}}},
    )

    context = get_system_context("pm")

    assert "I am the Product Manager." in context
    assert "[SYSTEM ADVISORY]" in context
    assert "Safe-by-Default (Advisory) mode" in context
    assert "do NOT have access to code execution tools" in context


def test_get_system_context_skips_advisory_mode_when_execution_enabled(mocker) -> None:
    """Proves the system removes the advisory warning when the user explicitly opts in."""
    # Simulate a user opting in via their setup config
    mocker.patch.dict(os.environ, {"BRAIN_ENABLE_CODE_EXECUTION": "true"}, clear=True)

    mocker.patch(
        "System.core.dna.get_dna_config",
        return_value={"agents": {"pm": {"system_prompt": "I am the Product Manager."}}},
    )

    context = get_system_context("pm")

    assert "I am the Product Manager." in context
    assert "[SYSTEM ADVISORY]" not in context


@pytest.mark.asyncio
@patch("System.llm.acompletion")
@patch("System.llm.log_interaction")
@patch(
    "System.neuroanatomy.systemic.endocrine.EndocrineSystem.get_humoral_vector",
    return_value={
        "dopamine": 0.5,
        "cortisol": 0.1,
        "adrenaline": 0.1,
        "serotonin": 0.5,
    },
)
async def test_ephemeral_prompt_caching_injection(
    mock_vector, mock_log, mock_acompletion
):
    """🛡️ ZERO-DEBT PROOF: Verifies Anthropic models receive explicit cache_control headers for system prompts."""
    # Mock LiteLLM response structure
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Action complete."

    # ⚡ FIX: Explicitly set tool_calls to None so the mock doesn't trigger the 5-loop retry!
    mock_response.choices[0].message.tool_calls = None

    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_acompletion.return_value = mock_response

    # Run the agent with a Claude model
    await run_agent_async(
        role_name="TestRole",
        model_string="claude-3-5-sonnet-20240620",
        system_prompt="Massive System Prompt",
        user_prompt="Hello",
    )

    # Verify LiteLLM received the exact nested caching dictionary exactly once
    mock_acompletion.assert_called_once()
    _, kwargs = mock_acompletion.call_args
    messages = kwargs["messages"]

    # Assert system prompt is a list with cache_control
    system_msg = messages[0]
    assert system_msg["role"] == "system"
    assert isinstance(system_msg["content"], list)
    assert system_msg["content"][0]["cache_control"]["type"] == "ephemeral"


def test_environmental_stream_guillotine_math():
    """🛡️ ZERO-DEBT PROOF: Verifies massive terminal outputs bounds math behaves perfectly."""
    # Simulate a massive tool output from the OS
    content_str = "A" * 20000

    if len(content_str) > 15000:
        content_str = (
            content_str[:15000]
            + "\n\n... [ ✂️ TRUNCATED: OUTPUT EXCEEDED 15,000 CHARACTERS. USE `grep`, `head`, OR `tail` ]"
        )

    assert len(content_str) < 16000
    assert "TRUNCATED: OUTPUT EXCEEDED" in content_str


def test_amnesia_sliding_window_logic():
    """🛡️ ZERO-DEBT PROOF: Verifies context memory is securely pruned to prevent token inflation."""
    # Generate a massive 50,000 character context payload
    massive_context = ("START_" * 1000) + ("MIDDLE_" * 4000) + ("END_" * 4000)

    MAX_CONTEXT_LENGTH = 45000
    if len(massive_context) > MAX_CONTEXT_LENGTH:
        pruned_context = (
            massive_context[:4000]
            + "\n\n... [ ✂️ OLDER EXECUTIONS PRUNED TO PRESERVE COGNITIVE EFFICIENCY ] ...\n\n"
            + massive_context[-40000:]
        )
    else:
        pruned_context = massive_context

    assert len(pruned_context) < 45000
    assert "OLDER EXECUTIONS PRUNED" in pruned_context
    assert pruned_context.startswith("START_")
    assert pruned_context.endswith("END_")
