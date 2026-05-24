# --- System/tools/execution/routing.py ---
import os
import sys
import shlex
import stat
import asyncio
from contextlib import asynccontextmanager

from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult
from System.ui.telemetry import render_command_cockpit

# ⚡ GLOBAL MODULE IMPORTS: Flattened dependency tree with zero hidden inline imports
import System.neuroanatomy.systemic.blood_brain_barrier as bbb
import System.neuroanatomy.limbic.amygdala as amygdala
import System.tools.sandbox as sandbox_module
import System.neuroanatomy.autonomic.vestibular as vestibular
import System.neuroanatomy.systemic.microglia as microglia
from System.neuroanatomy.sensory.somatosensory import SensoryTransducer
import System.tools.execution.validation as validation
import System.tools.execution.staging as staging


@asynccontextmanager
async def secure_execution_middleware(
    command_str: str, directory_path: str, parsed_args: list, effective_binaries: set
):
    """🛡️ SECURITY MIDDLEWARE: Encapsulates BBB validation, Amygdala heuristics, AST snapshots, and core isolation."""
    # ⚡ ZERO-DEBT: Direct module prefixing guarantees Pytest can dynamically intercept the mock targets
    is_safe_path, path_result = bbb.validate_execution_path(directory_path)
    if not is_safe_path:
        yield (
            False,
            ExecutionResult(
                success=False,
                output=f"<shell_output>\n<stderr>\n{path_result}\n</stderr>\n</shell_output>",
                block_reason=path_result,
            ),
        )
        return

    is_safe_cmd, threat_reason = amygdala.scan_command(command_str)
    if not is_safe_cmd:
        yield (
            False,
            ExecutionResult(
                success=False,
                output=f"<shell_output>\n<stderr>\n{threat_reason}\n</stderr>\n</shell_output>",
                block_reason=threat_reason,
            ),
        )
        return

    args, created_snapshots, stage_err = staging.stage_ast_snapshots(
        parsed_args, effective_binaries, path_result
    )
    if stage_err is not None:
        yield False, stage_err
        return
    if args is None:
        yield (
            False,
            ExecutionResult(
                success=False,
                output="<shell_output>\n<stderr>\nStaging failed.\n</stderr>\n</shell_output>",
                block_reason="Staging Error",
            ),
        )
        return

    vestibular.create_snapshot(directory_path)
    sys.modules["System.tools.execution"]._set_system_volume_mask(read_only=True)

    try:
        yield (
            True,
            {
                "args": args,
                "path_result": path_result,
                "created_snapshots": created_snapshots,
            },
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


async def execute_command_async(
    command: list[str] | str, directory_path: str, route: str = "UNKNOWN"
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

    execution_tier = os.environ.get("BRAIN_EXECUTION_TIER", "0")
    if route in sandbox_module.REQUIRES_CONTAINMENT:
        return await sandbox_module.execute_in_sandbox(
            parsed_args,
            normalize_path(ROOT_DIR / directory_path),
            env_secrets={},
            route=route,
        )

    async with secure_execution_middleware(
        command_str, directory_path, parsed_args, effective_binaries
    ) as (is_secure, context_data):
        if not is_secure:
            return context_data

        args = context_data["args"]
        path_result = context_data["path_result"]
        created_snapshots = context_data["created_snapshots"]
        exec_mod = sys.modules["System.tools.execution"]

        if os.environ.get("BRAIN_OS_HEADLESS") != "1":
            panel = render_command_cockpit(
                command_str,
                path_result,
                effective_binaries,
                created_snapshots,
                execution_tier,
                ROOT_DIR,
            )
            exec_mod.console.print("\n")
            exec_mod.console.print(panel)

            try:
                auth = await asyncio.to_thread(
                    input, "↳ Synaptic Authorization Handle [y/N]: "
                )
                auth = auth.strip().lower()
            except (EOFError, KeyboardInterrupt):
                auth = "n"

            if auth not in ["y", "yes"]:
                exec_mod.console.print(
                    "\n[bold red]❌ TRANSMISSION ABORTED: Security boundary held.[/bold red]\n"
                )
                return ExecutionResult(
                    success=False,
                    output="<shell_output>\n<stderr>\nSECURITY BLOCK: User denied execution.\n</stderr>\n</shell_output>",
                    block_reason="Denied",
                )
            else:
                exec_mod.console.print(
                    "\n[bold green]⚡ TRANSMISSION AUTHORIZED: Firing synaptic process tree...[/bold green]\n"
                )

        env_vars = exec_mod._get_scrubbed_env()

        try:
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

            timeout = 300.0 if "pytest" in command_str else 60.0
            timed_out, full_output = await exec_mod._stream_and_prune_process(
                process, timeout=timeout
            )

            if timed_out:
                exec_mod._rollback_workspace_transaction(path_result)
                return ExecutionResult(
                    success=False,
                    output="<shell_output>\n<stderr>\nERROR: Command timed out.\n</stderr>\n</shell_output>",
                    block_reason="Timeout",
                )

            if process.returncode != 0:
                exec_mod._rollback_workspace_transaction(path_result)
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
            exec_mod._rollback_workspace_transaction(path_result)
            return ExecutionResult(
                success=False,
                output=f"<shell_output>\n<stderr>\nEXECUTION ERROR: {str(e)}\n</stderr>\n</shell_output>",
                block_reason="Crash",
            )
