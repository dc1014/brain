# --- System/tools/execution/routing.py ---
import os
import sys
import shlex
import stat
import asyncio

from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult

# Flattened dependency tree and clean utility imports (No sys.modules hacks)
import System.neuroanatomy.systemic.blood_brain_barrier as bbb
import System.neuroanatomy.limbic.amygdala as amygdala
import System.tools.sandbox as sandbox_module
import System.neuroanatomy.autonomic.vestibular as vestibular
import System.neuroanatomy.systemic.microglia as microglia
from System.neuroanatomy.sensory.somatosensory import SensoryTransducer
import System.tools.execution.validation as validation
import System.tools.execution.staging as staging
from System.tools.execution.execution_utils import (
    set_system_volume_mask,
    rollback_workspace_transaction,
    get_scrubbed_env,
    stream_and_prune_process,
)


# Pure execution. Auth and timeouts are handled upstream.
async def execute_command_async(
    command: list[str] | str,
    directory_path: str,
    route: str = "UNKNOWN",
    timeout: float = 60.0,
) -> ExecutionResult:
    command_str = command if isinstance(command, str) else shlex.join(command)

    parsed_args, effective_binaries, parse_err = validation.parse_and_validate_args(
        command
    )
    if parse_err is not None:
        return parse_err
    if parsed_args is None or effective_binaries is None:
        return ExecutionResult(
            success=False,
            output="<shell_output>\n<stderr>\nInternal parsing error.\n</stderr>\n</shell_output>",
            block_reason="Parse Error",
        )

    if route in sandbox_module.REQUIRES_CONTAINMENT:
        return await sandbox_module.execute_in_sandbox(
            parsed_args,
            normalize_path(ROOT_DIR / directory_path),
            env_secrets={},
            route=route,
        )

    is_safe_path, path_result = bbb.validate_execution_path(directory_path)
    if not is_safe_path:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>",
            block_reason=path_result,
        )

    is_safe_cmd, threat_reason = amygdala.scan_command(command_str)
    if not is_safe_cmd:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{threat_reason}\n</stderr>\n</shell_output>",
            block_reason=threat_reason,
        )

    args, created_snapshots, stage_err = staging.stage_ast_snapshots(
        parsed_args, effective_binaries, path_result
    )
    if stage_err is not None:
        return stage_err
    if args is None:
        return ExecutionResult(
            success=False,
            output="<shell_output>\n<stderr>\nStaging failed.\n</stderr>\n</shell_output>",
            block_reason="Staging Error",
        )

    vestibular.create_snapshot(directory_path)
    set_system_volume_mask(read_only=True)

    try:
        env_vars = get_scrubbed_env()
        if sys.platform == "win32":
            process = await asyncio.create_subprocess_exec(
                args[0],
                *args[1:],
                cwd=path_result,
                env=env_vars,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                creationflags=0x01000000 | 0x00000200,
            )
        else:
            wrapped_cmd = f"ulimit -v 524288 -u 50 && exec {shlex.join(args)}"
            process = await asyncio.create_subprocess_exec(
                "sh",
                "-c",
                wrapped_cmd,
                cwd=path_result,
                env=env_vars,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

        timed_out, full_output = await stream_and_prune_process(
            process, timeout=timeout
        )

        if timed_out:
            rollback_workspace_transaction(path_result)
            return ExecutionResult(
                success=False,
                output="<shell_output>\n<stderr>\nERROR: Command timed out.\n</stderr>\n</shell_output>",
                block_reason="Timeout",
            )

        if process.returncode != 0:
            rollback_workspace_transaction(path_result)
            healed, heal_msg = await microglia.trigger_immune_response_async(
                command_str, full_output, path_result
            )
            if healed:
                return ExecutionResult(
                    success=True,
                    output=f"<shell_output>\n<stdout>\n{heal_msg}\n</stdout>\n</shell_output>",
                )
            else:
                compacted_err = SensoryTransducer().compact_terminal_output(
                    parsed_args, full_output
                )
                return ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{compacted_err}\n\nMicroglia Failed:\n{heal_msg}\n</stderr>\n</shell_output>",
                    block_reason="Failed",
                )

        compacted_output = SensoryTransducer().compact_terminal_output(
            parsed_args, full_output
        )
        return ExecutionResult(
            success=True,
            output=f"<shell_output>\n<stdout>\n{compacted_output}\n</stdout>\n</shell_output>",
        )

    except Exception as e:
        rollback_workspace_transaction(path_result)
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\nEXECUTION ERROR: {str(e)}\n</stderr>\n</shell_output>",
            block_reason="Crash",
        )
    finally:
        set_system_volume_mask(read_only=False)
        for snapshot in created_snapshots:
            try:
                if os.path.exists(snapshot):
                    os.chmod(snapshot, stat.S_IWRITE)
                    os.remove(snapshot)
            except Exception:
                pass
