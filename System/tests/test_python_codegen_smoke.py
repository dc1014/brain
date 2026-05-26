from __future__ import annotations

import json
from types import SimpleNamespace
from itertools import count

import pytest

from System.core.schemas import AgentResponseSchema, ToolCallSchema


@pytest.mark.asyncio
async def test_agent_can_generate_simple_python_file_with_object_tool_parameters(
    mocker, tmp_path
) -> None:
    """Smoke test the real JSON->MotorCortex write path for simple Python codegen."""
    import System.llm as llm
    import System.tools.file_system as file_system
    import System.tools.sandbox as sandbox

    mocker.patch.object(file_system, "ROOT_DIR", tmp_path)
    mocker.patch.object(sandbox, "ROOT_DIR", tmp_path)
    (tmp_path / "Studio").mkdir()

    mocker.patch.object(llm, "LOG_DIR", tmp_path / "logs")
    llm.LOG_DIR.mkdir(exist_ok=True)
    mocker.patch.object(llm, "LOG_FILE", llm.LOG_DIR / "agent_interactions.jsonl")
    mocker.patch("System.llm.get_current_metabolism", return_value={"exhausted": False})
    mocker.patch(
        "System.llm.apply_humoral_modulation", return_value=("mock", 0.0, 4000)
    )
    mocker.patch("System.llm.log_interaction", new_callable=mocker.AsyncMock)
    mocker.patch("System.llm.vault.resolve_routing", return_value=("mock", ""))
    mocker.patch("System.llm.vault.get_secret", return_value="")
    mocker.patch("System.llm.vault.mask_secrets", side_effect=lambda value: value)

    target = "Studio/simple_codegen/hello.py"
    source = (
        'def greet(name: str) -> str:\n    return f"Hello, {name}!"\n\n'
        'if __name__ == "__main__":\n    print(greet("CoreTex"))\n'
    )

    first_response = AgentResponseSchema(
        thought_process="Create the requested simple Python file.",
        final_response=None,
        tool_calls=[
            ToolCallSchema(
                tool_name="write_safe_file",
                parameters=json.dumps({"filepath": target, "content": source}),
                reasoning="Write the generated Python file to disk.",
            )
        ],
    )
    final_response = AgentResponseSchema(
        thought_process="The file exists now.", final_response="Created hello.py."
    )

    completion_calls = count(1)

    async def fake_completion(**kwargs):
        call_number = next(completion_calls)
        content = (
            first_response.model_dump_json()
            if call_number == 1
            else final_response.model_dump_json()
        )
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content, tool_calls=None)
                )
            ],
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=7),
        )

    mocker.patch("System.llm.acompletion", side_effect=fake_completion)

    result = await llm.run_agent_async(
        role_name="Codegen Smoke",
        model_string="mock",
        system_prompt="Generate code by calling write_safe_file.",
        user_prompt="Create a simple Python hello file.",
        route="CODE_GENERATION",
        domain="STUDIO",
        tools=[{"type": "function", "function": {"name": "write_safe_file"}}],
    )

    output_path = tmp_path / target
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == source
    assert "[WRITE_SAFE_FILE] Executed." in result.actions
    assert "Created hello.py" in result.text


@pytest.mark.asyncio
async def test_agent_still_accepts_legacy_stringified_tool_parameters(mocker) -> None:
    """Legacy stringified tool-call parameters still execute for existing prompts/logs."""
    from System.neuroanatomy.cortical.motor_cortex import execute_tools

    mock_write = mocker.patch("System.tools.write_safe_file", return_value="SUCCESS")

    messages, actions, halt_text = await execute_tools(
        [
            ToolCallSchema(
                tool_name="write_safe_file",
                parameters=json.dumps(
                    {"filepath": "Studio/legacy.py", "content": "print('ok')\n"}
                ),
                reasoning="legacy compatibility",
            )
        ],
        role_name="Codegen Smoke",
        route="CODE_GENERATION",
    )

    mock_write.assert_called_once_with(
        filepath="Studio/legacy.py", content="print('ok')\n"
    )
    assert messages[0]["name"] == "write_safe_file"
    assert "[WRITE_SAFE_FILE] Executed" in actions[0]
    assert halt_text == ""
