import asyncio
from unittest.mock import MagicMock
from System.neuroanatomy.cortical.motor_cortex import MotorCortex, execute_tools


def test_motor_cortex_locking():
    """Ensure resolving paths creates identical locks for the same physical file."""
    lock1 = MotorCortex.get_lock("Studio/app.py")
    lock2 = MotorCortex.get_lock("./Studio/app.py")
    lock3 = MotorCortex.get_lock("Personal/notes.md")

    # Identical resolved paths must share the exact same lock in memory
    assert lock1 is lock2
    assert lock1 is not lock3


def test_execute_tools_missing_tool():
    """Ensure unknown tools return a graceful error and don't crash the loop."""
    mock_call = MagicMock()
    mock_call.function.name = "hallucinated_tool"
    mock_call.function.arguments = "{}"
    mock_call.id = "call_123"

    tool_msgs, actions, halt_text = asyncio.run(execute_tools([mock_call], "Agent"))

    assert len(tool_msgs) == 1
    assert "ERROR: Unknown tool 'hallucinated_tool'" in tool_msgs[0]["content"]
    assert halt_text == ""


def test_execute_tools_success_and_write_lock(mocker):
    """Ensure write tools execute safely and record success."""
    mock_call = MagicMock()
    mock_call.function.name = "write_safe_file"
    mock_call.function.arguments = '{"filepath": "test.txt", "content": "hello"}'
    mock_call.id = "call_write"

    # Mock the actual tool
    mocker.patch("System.tools.write_safe_file", return_value="SUCCESS: Wrote file")

    tool_msgs, actions, halt_text = asyncio.run(execute_tools([mock_call], "Agent"))

    assert len(tool_msgs) == 1
    assert "SUCCESS: Wrote file" in tool_msgs[0]["content"]
    assert "[WRITE_SAFE_FILE] Executed successfully." in actions[0]


def test_execute_tools_security_block(mocker):
    """Ensure a SECURITY BLOCK returned by a tool triggers the systemic halt."""
    mock_call = MagicMock()
    mock_call.function.name = "execute_command"
    mock_call.function.arguments = '{"command": "rm -rf /", "directory_path": "."}'
    mock_call.id = "call_bad"

    mocker.patch("System.tools.execute_command", return_value="SECURITY BLOCK: Denied.")

    tool_msgs, actions, halt_text = asyncio.run(execute_tools([mock_call], "Agent"))

    assert "[SYSTEM HALT]" in halt_text
    assert "SECURITY BLOCK" in halt_text
    assert "[HALTED]" in actions[0]


def test_execute_tools_truncation(mocker):
    """Ensure massive tool outputs are mathematically truncated to 8000 chars to protect the context window."""
    mock_call = MagicMock()
    mock_call.function.name = "read_safe_file"
    mock_call.function.arguments = '{"filepath": "huge.log"}'
    mock_call.id = "call_huge"

    # Mock a massive 15,000 character return string
    massive_string = "A" * 15000
    mocker.patch("System.tools.read_safe_file", return_value=massive_string)

    tool_msgs, actions, halt_text = asyncio.run(execute_tools([mock_call], "Agent"))

    content = tool_msgs[0]["content"]
    assert len(content) < 15000
    assert "[SYSTEM WARNING: Truncated" in content
