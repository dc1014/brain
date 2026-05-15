import asyncio
import json
from typing import Any, Dict, Tuple, Union
from pathlib import Path
from rich.console import Console
import System.tools as os_tools
from System.core.schemas import ExecutionResult

console = Console()


class MotorCortex:
    # Maps (loop_id, resolved_path_string) to an asyncio.Lock to prevent cross-loop seizures
    _locks: Dict[Tuple[int, str], asyncio.Lock] = {}

    @classmethod
    def get_lock(cls, file_path: Union[str, Path]) -> asyncio.Lock:
        """
        Lazy-loads an asyncio Lock bound strictly to the current active event loop.
        Zero Debt: Prevents 'attached to a different loop' crashes across CLI commands.
        """
        try:
            loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            loop_id = 0

        # SHIFT-LEFT FIX: Use .absolute() instead of .resolve() to bypass Windows filesystem quirks.
        # This guarantees deterministic lock matching for the exact same path string.
        resolved_path = str(Path(file_path).absolute())

        key = (loop_id, resolved_path)
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

        is_halted = False
        raw_output = ""

        try:
            if not hasattr(os_tools, func_name):
                raw_output = f"ERROR: Unknown tool '{func_name}' in System.tools"
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

                # ⚡ SHIFT-LEFT: Strongly-Typed Result Parsing
                if isinstance(result, ExecutionResult):
                    raw_output = result.output
                    if not result.success:
                        action_manifest.append("[HALTED] Security clearance denied.")
                        system_halt_text = (
                            f"\n\n[SYSTEM HALT] {result.block_reason or raw_output}"
                        )
                        is_halted = True
                    else:
                        action_manifest.append(
                            f"[{func_name.upper()}] Executed successfully."
                        )
                else:
                    # Legacy string fallback for tools we haven't migrated yet
                    raw_output = str(result)
                    if (
                        raw_output.startswith("SECURITY BLOCK")
                        or "<stderr>\nSECURITY BLOCK" in raw_output
                    ):
                        action_manifest.append("[HALTED] Security clearance denied.")
                        system_halt_text = f"\n\n[SYSTEM HALT] {raw_output}"
                        is_halted = True
                    else:
                        action_manifest.append(
                            f"[{func_name.upper()}] Executed successfully."
                        )

        except Exception as e:
            raw_output = f"ERROR executing {func_name}: {str(e)}"

        console.print(f"[dim]🔍 Tool Executed: {func_name}[/dim]")

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

        if is_halted:
            break

    return tool_messages, action_manifest, system_halt_text
