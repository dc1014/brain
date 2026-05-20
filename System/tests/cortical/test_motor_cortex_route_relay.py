import pytest
import json
from unittest.mock import MagicMock
from System.neuroanatomy.cortical.motor_cortex import execute_tools
import System.tools as os_tools


@pytest.mark.asyncio
async def test_motor_cortex_relays_route_to_execution_tools(monkeypatch, mocker):
    """
    Zero-Debt Test: Proves that execute_tools correctly appends the `route` parameter
    to execution commands so downstream execution tools can enforce the Containment Matrix.
    """
    # 1. Create a dummy tool call payload simulating an LLM Agent wanting to run a shell command
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "execute_shell_command"
    mock_tool_call.function.arguments = json.dumps(
        {"command": "echo 'Testing the sandbox relay'"}
    )

    # 2. Mock the actual execution tool to intercept the payload before it runs
    mock_execute = mocker.MagicMock()

    from System.core.schemas import ExecutionResult

    mock_execute.return_value = ExecutionResult(success=True, output="Mock Output")
    monkeypatch.setattr(os_tools, "execute_shell_command", mock_execute, raising=False)

    # 3. Call execute_tools, passing the highly lethal SWARM route
    await execute_tools([mock_tool_call], "test_agent", step_index=0, route="SWARM")

    # 4. Strict Validation: The route string MUST be injected into the tool's keyword arguments
    mock_execute.assert_called_once_with(
        command="echo 'Testing the sandbox relay'", route="SWARM"
    )
