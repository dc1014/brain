# --- System/tools/sandbox.py ---
import os
import json
import shlex
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Set, Any
from rich.console import Console

from System.core.paths import ROOT_DIR, normalize_path
from System.core.schemas import ExecutionResult
from System.tools.microsandbox import (
    get_pre_warmed_worker,
    replenish_worker_pool_detached,
)

console = Console()

# Define the global stream limit
MAX_BYTES = 5 * 1024 * 1024  # 5 MB ceiling

# =====================================================================
# 🛡️ SHIFT LEFT SECURITY: DYNAMIC OS DIRECTORY BOUNDARY PROXIES
# =====================================================================


class DynamicDirectorySet:
    def __init__(self, relative_segments: list[str]) -> None:
        self._relative_segments = relative_segments

    def _resolve(self) -> Set[Path]:
        return {
            normalize_path(ROOT_DIR / segment) for segment in self._relative_segments
        }

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)

    def __contains__(self, item: Any) -> bool:
        return item in self._resolve()

    def __iter__(self) -> Any:
        return iter(self._resolve())

    def __len__(self) -> int:
        return len(self._resolve())

    def __repr__(self) -> str:
        return repr(self._resolve())


ALLOWED_DIRECTORIES = DynamicDirectorySet(
    [
        "Personal",
        "Professional",
        "Studio",
        "Meta",
        "Media",
        "System/config",
        "System/logs",
    ]
)
READ_ONLY_DIRECTORIES = DynamicDirectorySet(["System"])

_INITIAL_ROOT_DIR = normalize_path(ROOT_DIR)


def _is_windows_junction(path: Path) -> bool:
    if os.name == "nt" and path.is_dir():
        try:
            import ctypes

            # ⚡ FIXED: Added explicit mypy ignore rule to survive Linux CI environment static analysis passes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))  # type: ignore[attr-defined]
            return attrs != -1 and bool(attrs & 0x400)
        except Exception:
            pass
    return False


def is_safe_path(target_path: Path | str, require_write: bool = False) -> bool:
    resolved_target = normalize_path(target_path)
    current_root = normalize_path(ROOT_DIR)

    if resolved_target.exists():
        if resolved_target.is_symlink() or _is_windows_junction(resolved_target):
            return False

    for parent in resolved_target.parents:
        if parent == current_root:
            break
        if parent.is_symlink() or _is_windows_junction(parent):
            return False

    actual_allowed: Set[Path] = set()
    actual_readonly: Set[Path] = set()

    has_initial_paths = any(
        str(_INITIAL_ROOT_DIR).lower() in str(d).lower() for d in ALLOWED_DIRECTORIES
    )

    if current_root == _INITIAL_ROOT_DIR or not has_initial_paths:
        actual_allowed.update(ALLOWED_DIRECTORIES)
        actual_readonly.update(READ_ONLY_DIRECTORIES)
    else:
        for d in ALLOWED_DIRECTORIES:
            try:
                rel = d.relative_to(_INITIAL_ROOT_DIR)
                actual_allowed.add(normalize_path(current_root / rel))
            except ValueError:
                actual_allowed.add(normalize_path(d))
        for d in READ_ONLY_DIRECTORIES:
            try:
                rel = d.relative_to(_INITIAL_ROOT_DIR)
                actual_readonly.add(normalize_path(current_root / rel))
            except ValueError:
                actual_readonly.add(normalize_path(d))

    for allowed_dir in actual_allowed:
        try:
            resolved_target.relative_to(allowed_dir)
            return True
        except ValueError:
            continue

    if not require_write:
        for ro_dir in actual_readonly:
            try:
                resolved_target.relative_to(ro_dir)
                return True
            except ValueError:
                continue

    return False


def _get_directory_size(path: Path) -> int:
    """Calculates the raw byte weight of a directory."""
    total_size = 0
    try:
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except Exception:
        pass
    return total_size


# =====================================================================
# 🐳 THE CONTAINMENT MATRIX (SHELL EXECUTION ISOLATION)
# =====================================================================

REQUIRES_CONTAINMENT: Set[str] = {
    "SWARM",
    "STATIC_PAGE",
    "CODE_GENERATION",
}

ALLOWED_NATIVE_ROUTES: Set[str] = {
    "WORKSPACE",
    "DOCUMENTATION",
    "ANALYTICS",
}


async def execute_in_sandbox(
    command: list[str] | str,
    workspace_path: Path,
    env_secrets: Dict[str, str],
    route: str = "UNKNOWN",
) -> ExecutionResult:

    # 🔐 SAFE-BY-DEFAULT: Global kill-switch for autonomous code execution. Must be explicitly opted-in.
    code_execution_enabled = os.environ.get(
        "BRAIN_ENABLE_CODE_EXECUTION", "false"
    ).lower() in ("true", "1", "yes")

    if not is_safe_path(workspace_path, require_write=True):
        return ExecutionResult(
            success=False,
            output="",
            block_reason="CRITICAL SECURITY TERMINATION: Attempted out-of-bounds workspace execution access.",
        )

    # ⚡ ZERO-DEBT FIXED: Initialize and normalize parsed_args at the top function scope
    if isinstance(command, str):
        parsed_args = shlex.split(command)
    else:
        parsed_args = [str(arg) for arg in command]

    if route in REQUIRES_CONTAINMENT:
        # 🛡️ THE GATEKEEPER: Abort instantly if the user hasn't enabled code execution
        if not code_execution_enabled:
            console.print(
                f"\n[bold red]❌ SECURITY BLOCK: Containment requested for route '{route}', but execution is disabled.[/bold red]"
            )
            console.print(
                "[dim]For your safety, Brain OS runs in a read-only state by default. To enable autonomous execution, set BRAIN_ENABLE_CODE_EXECUTION=true.[/dim]\n"
            )
            return ExecutionResult(
                success=False,
                output="",
                block_reason="OPT-IN REQUIRED: Autonomous code execution is disabled by default.",
            )

        console.print(
            f"[bold cyan]🔒 Embedded Containment Matrix Active (Route: {route}): Enforcing Cryptographic WASM Jail...[/bold cyan]"
        )

        is_inline = "-c" in parsed_args
        inline_code = ""
        target_script = ""

        if is_inline:
            try:
                idx = parsed_args.index("-c")
                inline_code = parsed_args[idx + 1]
            except Exception:
                pass
        else:
            target_script = next(
                (arg for arg in parsed_args if arg.endswith((".js", ".ts", ".py"))), ""
            )

        has_deno = shutil.which("deno") is not None

        if not has_deno:
            return ExecutionResult(
                success=False,
                output="",
                block_reason="CRITICAL SECURITY TERMINATION: Deno runtime is required for secure WebAssembly isolation. Please install Deno.",
            )

        # 🛡️ ZERO-DEBT: Separate URI schemas for JS imports vs. Pyodide internal loaders
        real_system_dir = Path(__file__).resolve().parent.parent
        vendor_resolved = normalize_path(
            real_system_dir / "vendor" / "pyodide"
        ).resolve()

        vendor_import_url = (
            vendor_resolved.as_uri()
        )  # file:///C:/... (For Deno JS import)
        vendor_index_path = (
            vendor_resolved.as_posix()
        )  # C:/... (For Pyodide internal FS loader)

        static_js_runner = f"""
// ⚡ 100% OFFLINE VENDOR LOAD: No network required.
import {{ createRequire }} from "node:module";
import {{ fileURLToPath }} from "node:url";
import {{ dirname }} from "node:path";

globalThis.require = createRequire(import.meta.url);
globalThis.__filename = fileURLToPath(import.meta.url);
globalThis.__dirname = dirname(globalThis.__filename);

// Deno requires the strict file:/// URI for module importing
import {{ loadPyodide }} from "{vendor_import_url}/pyodide.mjs";

async function runWasmPython() {{
    try {{
        const isInline = {json.dumps(bool(inline_code))};
        let code = "";

        if (isInline) {{
            code = {json.dumps(inline_code)};
        }} else {{
            const targetPath = {json.dumps(target_script)};
            if (!targetPath) {{
                console.log('User-space V8 sandbox verified.');
                Deno.exit(0);
            }}
            code = Deno.readTextFileSync(targetPath);
        }}

        // Pyodide requires the raw POSIX path to locate WASM binaries via Node FS APIs
        const pyodide = await loadPyodide({{
            indexURL: "{vendor_index_path}/",
            env: {json.dumps(env_secrets)}
        }});

        // 🛡️ ZERO-DEBT: Lobotomize the FFI (Foreign Function Interface)
        // We explicitly block Python from accessing the JavaScript host environment
        // by blackholing the Pyodide JS bindings before the user code runs.
        await pyodide.runPythonAsync(`
import sys
sys.modules['js'] = None
sys.modules['pyodide_js'] = None
sys.modules['pyodide'] = None
`);

        pyodide.setStdout({{ batched: (msg) => console.log(msg) }});
        pyodide.setStderr({{ batched: (msg) => console.error(msg) }});

        await pyodide.runPythonAsync(code);

        console.log("[__EXECUTION_COMPLETE__]");

    }} catch (e) {{
        if (e.message && !e.message.includes('Requires read access')) {{
            console.error("WASM Sandbox Exception:\\n", e.message);
            throw new Error("Sandbox Isolation Failure");
        }}
    }}
}}
runWasmPython();
"""

        try:
            proc = await get_pre_warmed_worker(workspace_path)

            if proc.stdin:
                proc.stdin.write(static_js_runner.encode("utf-8"))
                await proc.stdin.drain()
                proc.stdin.close()

            output_chunks = []
            bytes_read = 0
            execution_completed = False

            # 🛡️ DEFCON PROOF 11: The Storage Guillotine
            initial_disk_weight = _get_directory_size(workspace_path)
            MAX_INFLATION_BYTES = 100 * 1024 * 1024

            async def _monitor_storage():
                while proc.returncode is None:
                    current_weight = _get_directory_size(workspace_path)
                    if current_weight - initial_disk_weight > MAX_INFLATION_BYTES:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        output_chunks.append(
                            b"\n\n[CRITICAL SECURITY BLOCK: Disk Storage Exhaustion Prevented. Process killed due to excessive disk writes.]"
                        )
                        break
                    await asyncio.sleep(0.5)

            async def _read_stream():
                nonlocal bytes_read, execution_completed
                if proc.stdout is None:
                    return
                while True:
                    chunk = await proc.stdout.read(8192)
                    if not chunk:
                        break

                    bytes_read += len(chunk)

                    if b"[__EXECUTION_COMPLETE__]" in chunk:
                        execution_completed = True
                        output_chunks.append(
                            chunk.replace(b"[__EXECUTION_COMPLETE__]", b"")
                        )
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        break

                    output_chunks.append(chunk)
                    if bytes_read > MAX_BYTES:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        output_chunks.append(
                            b"\n\n[CRITICAL SECURITY BLOCK: WASM Output Stream Exceeded 5MB Capacity. Pipe Bomb Prevented.]"
                        )
                        break

            storage_task = asyncio.create_task(_monitor_storage())

            try:
                await asyncio.wait_for(_read_stream(), timeout=60.0)
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                output_chunks.append(
                    b"\n\n[CRITICAL SECURITY BLOCK: WASM Execution Timeout Exceeded 60s. Infinite Loop Pruned.]"
                )

            await proc.wait()
            storage_task.cancel()

            output_str = b"".join(output_chunks).decode(errors="replace")
            replenish_worker_pool_detached(workspace_path)

            # ⚡ SHIFT-LEFT TOKEN ECONOMICS: Apply deterministic compaction to WASM streams
            from System.neuroanatomy.sensory.somatosensory import SensoryTransducer

            output_str = SensoryTransducer().compact_terminal_output(
                parsed_args, output_str
            )

            # 🛡️ THE SECRET SCRUBBER: Shift-Left Data Leak Prevention
            if env_secrets:
                for secret_key, secret_value in env_secrets.items():
                    # Only scrub meaningful secrets to prevent accidental stripping of common chars like '0' or 'A'
                    if secret_value and len(secret_value) > 4:
                        output_str = output_str.replace(
                            secret_value, f"[REDACTED_SECRET:{secret_key}]"
                        )

            is_success = execution_completed or proc.returncode == 0
            return ExecutionResult(
                success=is_success,
                output=output_str,
                block_reason=None
                if is_success
                else f"Sandbox execution failed with exit code {proc.returncode}",
            )

        except Exception as e:
            replenish_worker_pool_detached(workspace_path)
            return ExecutionResult(
                success=False,
                output="",
                block_reason=f"User-space micro-sandbox pool execution failure: {str(e)}",
            )

    elif route in ALLOWED_NATIVE_ROUTES:
        console.print(
            f"[dim]⚡ Native Execution Authorized (Route: {route}). Bypassing Tier 1 Container.[/dim]"
        )
        from System.tools.execution import execute_native_isolated

        result = await execute_native_isolated(parsed_args, workspace_path, env_secrets)

        # ⚡ SHIFT-LEFT TOKEN ECONOMICS: Compact native sandbox bypass route output streams
        from System.neuroanatomy.sensory.somatosensory import SensoryTransducer

        result.output = SensoryTransducer().compact_terminal_output(
            parsed_args, result.output
        )
        return result

    else:
        return ExecutionResult(
            success=False,
            output="",
            block_reason=f"CRITICAL SECURITY BLOCK: Route '{route}' is not explicitly whitelisted for execution.",
        )
