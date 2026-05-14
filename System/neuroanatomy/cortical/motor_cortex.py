import asyncio
import json
from pathlib import Path
from typing import Any
from rich.console import Console
import System.tools as os_tools

console = Console()


class MotorCortex:
    """
    Coordinates file-system motor actions to prevent race conditions.
    Locks are securely bound to their specific event loop to prevent cross-loop contamination.
    """

    _locks: dict[str, asyncio.Lock] = {}

    @classmethod
    def get_lock(cls, filepath: str | Path) -> asyncio.Lock:
        try:
            loop = asyncio.get_running_loop()
            loop_id = str(id(loop))
        except RuntimeError:
            # SHIFT-LEFT: Graceful degradation for synchronous Pytest environments
            loop_id = "sync_test_loop"

        # Create a unique lock key based on the active event loop ID AND the file path
        key = f"{loop_id}_{str(Path(filepath).resolve())}"

        if key not in cls._locks:
            cls._locks[key] = asyncio.Lock()
        return cls._locks[key]


async def execute_tools(
    tool_calls: list[Any], role_name: str, step_index: int = 0
) -> tuple[list[dict[str, Any]], list[str], str]:
    """
    Executes a batch of tool calls securely, managing locks and formatting results.
    Returns: (tool_messages, action_manifest_additions, system_halt_text)
    """
    tool_messages = []
    action_manifest = []
    system_halt_text = ""

    if tool_calls and step_index == 0:
        console.print(f"\n[dim]⚡ {role_name} is thinking and acting...[/dim]")

    for tool_call in tool_calls:
        args = json.loads(tool_call.function.arguments)
        func_name = str(tool_call.function.name)
        tool_id = str(tool_call.id)

        try:
            if not hasattr(os_tools, func_name):
                result = f"ERROR: Unknown tool '{func_name}' in System.tools"
            else:
                tool_func = getattr(os_tools, func_name)

                WRITE_TOOLS = {
                    "write_safe_file",
                    "append_safe_file",
                    "delete_safe_file",
                    "rename_safe_file",
                    "copy_safe_file",
                }

                if func_name in WRITE_TOOLS:
                    target_path = (
                        args.get("filepath")
                        or args.get("dest_filepath")
                        or args.get("new_filepath")
                        or "global_write"
                    )
                    async with MotorCortex.get_lock(target_path):
                        result = await asyncio.to_thread(tool_func, **args)
                else:
                    result = await asyncio.to_thread(tool_func, **args)

                # ⚡ FIX: Only append success if the output does NOT contain a security block!
                if not (
                    str(result).startswith("SECURITY BLOCK")
                    or str(result).startswith(
                        "<shell_output>\n<stderr>\nSECURITY BLOCK"
                    )
                ):
                    action_manifest.append(
                        f"[{func_name.upper()}] Executed successfully."
                    )

        except Exception as e:
            result = f"ERROR executing {func_name}: {str(e)}"

        console.print(f"[dim]🔍 Tool Executed: {func_name}[/dim]")

        raw_output = str(result)
        MAX_CHARS = 8000
        truncated_output = raw_output[:MAX_CHARS] + (
            f"\n\n... [SYSTEM WARNING: Truncated at {MAX_CHARS} chars]"
            if len(raw_output) > MAX_CHARS
            else ""
        )

        tool_messages.append(
            {
                "role": "tool",
                "name": func_name,
                "tool_call_id": tool_id,
                "content": truncated_output,
            }
        )

        # Shift-Left Security: If a tool hits the Blood-Brain Barrier, halt everything.
        if str(result).startswith("SECURITY BLOCK") or str(result).startswith(
            "<shell_output>\n<stderr>\nSECURITY BLOCK"
        ):
            system_halt_text = f"\n\n[SYSTEM HALT] {result}"
            action_manifest.append("[HALTED] Security clearance denied.")
            break

    return tool_messages, action_manifest, system_halt_text
