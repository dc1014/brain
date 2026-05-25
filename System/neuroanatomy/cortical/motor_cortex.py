# --- System/neuroanatomy/cortical/motor_cortex.py ---
import asyncio
import json
import uuid
import inspect
from typing import Any, Dict, Tuple, Union

from pathlib import Path
from rich.console import Console

import System.tools as os_tools
from System.core.schemas import ExecutionResult, ToolCallSchema

console = Console()


class MotorCortex:
    _locks: Dict[Tuple[int, str], asyncio.Lock] = {}

    @classmethod
    def get_lock(cls, file_path: Union[str, Path]) -> asyncio.Lock:
        try:
            loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            loop_id = 0

        resolved_path = str(Path(file_path).absolute())
        key = (loop_id, resolved_path)
        if key not in cls._locks:
            cls._locks[key] = asyncio.Lock()
        return cls._locks[key]


async def execute_tools(
    tool_calls: list[Any], role_name: str, step_index: int = 0, route: str = "UNKNOWN"
) -> tuple[list[dict[str, Any]], list[str], str]:
    tool_messages: list[dict[str, Any]] = []
    action_manifest: list[str] = []
    system_halt_text: str = ""

    if tool_calls and step_index == 0:
        console.print(f"\n[dim]{role_name} is thinking and acting...[/dim]")

    for tool_call in tool_calls:
        if isinstance(tool_call, dict):
            if "tool_name" in tool_call:
                args = tool_call.get("parameters", {})
                func_name = str(tool_call["tool_name"])
            else:
                func_data = tool_call.get("function", {})
                args = func_data.get("arguments", {})
                func_name = str(func_data.get("name", ""))
            tool_id = str(tool_call.get("id", f"call_{uuid.uuid4().hex[:8]}"))

        elif isinstance(tool_call, ToolCallSchema):
            args = getattr(tool_call, "parameters", {})
            func_name = str(getattr(tool_call, "tool_name", "unknown"))
            tool_id = f"call_{uuid.uuid4().hex[:8]}"

        else:
            args = getattr(tool_call.function, "arguments", "{}")
            func_name = str(getattr(tool_call.function, "name", "unknown"))
            tool_id = str(getattr(tool_call, "id", f"call_{uuid.uuid4().hex[:8]}"))

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}

        if "path" in args and "filepath" not in args:
            args["filepath"] = args.pop("path")

        is_halted = False
        raw_output = ""

        try:
            # FIX: Check if the tool exists FIRST before enforcing strict parameter payloads
            if not hasattr(os_tools, func_name):
                raw_output = f"ERROR: Unknown tool '{func_name}' in System.tools"
            else:
                if not args and func_name not in ["get_time", "check_status"]:
                    raise ValueError(
                        f"SECURITY BLOCK: Missing required parameters for tool '{func_name}'. Received empty dictionary."
                    )

                tool_func = getattr(os_tools, func_name)

                WRITE_TOOLS = {
                    "write_safe_file",
                    "append_safe_file",
                    "delete_safe_file",
                    "rename_safe_file",
                    "copy_safe_file",
                }

                EXECUTION_TOOLS = {
                    "execute_shell_command",
                    "run_sandbox_command",
                    "execute_python_code",
                }
                if func_name in EXECUTION_TOOLS:
                    args["route"] = route

                async def _run_tool():
                    if inspect.iscoroutinefunction(tool_func):
                        return await tool_func(**args)
                    else:
                        return await asyncio.to_thread(tool_func, **args)

                if func_name in WRITE_TOOLS:
                    target_path = (
                        args.get("filepath")
                        or args.get("dest_filepath")
                        or args.get("new_filepath")
                        or "global_write"
                    )
                    async with MotorCortex.get_lock(target_path):
                        result = await _run_tool()
                else:
                    result = await _run_tool()

                if isinstance(result, ExecutionResult):
                    raw_output = result.output
                    is_security_block = (
                        not result.success
                        and result.block_reason
                        and "SECURITY BLOCK" in result.block_reason
                    )

                    if is_security_block:
                        action_manifest.append("[HALTED] Security clearance denied.")
                        system_halt_text = (
                            f"\n\n[SYSTEM HALT] {result.block_reason or raw_output}"
                        )
                        is_halted = True
                    else:
                        action_manifest.append(f"[{func_name.upper()}] Executed.")
                else:
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
            error_str = str(e)
            if "Security Block" in error_str or "SECURITY BLOCK" in error_str:
                raw_output = f"SECURITY BLOCK: {error_str}"
                action_manifest.append("[HALTED] Security clearance denied.")
                system_halt_text = f"\n\n[SYSTEM HALT] {raw_output}"
                is_halted = True
            else:
                raw_output = f"ERROR executing {func_name}: {error_str}"

        console.print(f"[dim]Tool Executed: {func_name}[/dim]")

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
