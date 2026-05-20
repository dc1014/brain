# --- System/tools/execution/routing.py ---
import os
import sys
import shlex
import stat
import asyncio
from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult

from .validation import parse_and_validate_args
from .OS.win32_jail import apply_windows_job_object


async def execute_command_async(
    command: str, directory_path: str, route: str = "UNKNOWN"
) -> ExecutionResult:
    from System.neuroanatomy.systemic.blood_brain_barrier import validate_execution_path
    from System.neuroanatomy.limbic.amygdala import scan_command

    is_safe_path_result, path_result = validate_execution_path(directory_path)
    if not is_safe_path_result:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>",
            block_reason=path_result,
        )

    is_safe_cmd, threat_reason = scan_command(command)
    if not is_safe_cmd:
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\n{threat_reason}\n</stderr>\n</shell_output>",
            block_reason=threat_reason,
        )

    parsed_args, effective_binaries, parse_err = parse_and_validate_args(command)
    if parse_err:
        return parse_err

    execution_tier = os.environ.get("BRAIN_EXECUTION_TIER", "0")
    from System.tools.sandbox import REQUIRES_CONTAINMENT, execute_in_sandbox

    if route in REQUIRES_CONTAINMENT:
        return await execute_in_sandbox(
            shlex.join(parsed_args),
            normalize_path(ROOT_DIR / directory_path),
            env_secrets={},
            route=route,
        )
    elif execution_tier == "1":
        import System.tools.execution as exec_pkg

        return exec_pkg._run_tier_1_microsandbox(
            shlex.join(parsed_args), normalize_path(ROOT_DIR / directory_path)
        )

    from .staging import stage_ast_snapshots

    args, created_snapshots, stage_err = stage_ast_snapshots(
        parsed_args, effective_binaries, path_result
    )
    if stage_err:
        return stage_err

    try:
        from System.neuroanatomy.autonomic.vestibular import create_snapshot

        create_snapshot(directory_path)

        if os.environ.get("BRAIN_OS_HEADLESS") != "1":
            try:
                auth = await asyncio.to_thread(input, "Allow execution? [y/N]: ")
            except (EOFError, KeyboardInterrupt):
                auth = "n"
            if auth.strip().lower() not in ["y", "yes"]:
                return ExecutionResult(
                    success=False,
                    output="<shell_output>\n<stderr>\nSECURITY BLOCK: User explicitly denied command execution.\n</stderr>\n</shell_output>",
                    block_reason="Denied",
                )

        # ⚡ THE ULTIMATE SPY ALIGNMENT: Explicitly pull from the global sys.modules cache
        # to ensure that Pytest's tracking interceptor records the mask engagement state accurately!
        sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=True)
        print(f"\n▶ Executing natively on host: {shlex.join(args)}")

        exec_mod = sys.modules["System.tools.execution"]
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=path_result,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=exec_mod._get_scrubbed_env(),
            **exec_mod._get_subprocess_kwargs(),
        )

        if sys.platform == "win32":
            try:
                apply_windows_job_object(process.pid)
            except Exception:
                pass

        timed_out, full_output = await exec_mod._stream_and_prune_process(
            process, timeout=180.0
        )
        sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=False)

        if timed_out:
            exec_mod._rollback_workspace_transaction(path_result)
            return ExecutionResult(
                success=False,
                output="<shell_output>\n<stderr>\nERROR: Command timed out. Process tree violently pruned.\n</stderr>\n</shell_output>",
                block_reason="Timeout",
            )

        if process.returncode != 0:
            exec_mod._rollback_workspace_transaction(path_result)
            from System.neuroanatomy.systemic.microglia import (
                trigger_immune_response_async,
            )

            healed, heal_msg = await trigger_immune_response_async(
                command, full_output, path_result
            )
            return (
                ExecutionResult(
                    success=True,
                    output=f"<shell_output>\n<stdout>\n{heal_msg}\n</stdout>\n</shell_output>",
                )
                if healed
                else ExecutionResult(
                    success=False,
                    output=f"<shell_output>\n<stderr>\n{full_output}\n\nMicroglia Antibody Failed:\n{heal_msg}\n</stderr>\n</shell_output>",
                    block_reason=f"Failed with exit code {process.returncode}",
                )
            )

        return ExecutionResult(
            success=True,
            output=f"<shell_output>\n<stdout>\n{full_output}\n</stdout>\n</shell_output>",
        )
    except Exception as e:
        sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=False)
        sys.modules["System.tools.execution"]._rollback_workspace_transaction(
            path_result
        )
        return ExecutionResult(
            success=False,
            output=f"<shell_output>\n<stderr>\nEXECUTION ERROR: {str(e)}\n</stderr>\n</shell_output>",
            block_reason="Crash",
        )
    finally:
        sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=False)
        for snapshot in created_snapshots:
            try:
                if os.path.exists(snapshot):
                    os.chmod(snapshot, stat.S_IWRITE)
                    os.remove(snapshot)
            except Exception:
                pass
