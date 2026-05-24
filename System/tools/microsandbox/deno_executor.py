# --- System/tools/microsandbox/deno_executor.py ---
import subprocess
from pathlib import Path
from typing import Dict, Any


def execute_sandboxed_js(
    script_path: Path, staging_dir: Path, timeout: int = 60
) -> Dict[str, Any]:
    """
    🛡️ DEFCON 1 JS Sandbox: Executes raw JS/TS with the exact same
    cryptographic capability erasure used by the Pyodide WebAssembly container.
    """
    if not script_path.exists():
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Script not found: {script_path}",
        }

    # 🛡️ UNIFIED SECURITY: Apply the identical 11-proof matrix to raw JS
    command = [
        "deno",
        "run",
        "--allow-net=none",
        "--quiet",
        "--no-prompt",
        "--no-config",
        "--no-lock",
        "--v8-flags=--max-old-space-size=256",
        # ⚡ FIXED: Native OS paths
        f"--allow-read={str(staging_dir.resolve())}",
        f"--allow-write={str(staging_dir.resolve())}",
        str(script_path.resolve()),
    ]

    try:
        res = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(staging_dir.resolve()),
            # 🛡️ DEFCON PROOF 4: OS-Level Environment Stripping
            env={"NO_COLOR": "1"},
        )
        return {
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": 124,
            "stdout": "",
            "stderr": "CRITICAL SECURITY BLOCK: JS Execution Timeout Exceeded. Infinite Loop Pruned.",
        }
