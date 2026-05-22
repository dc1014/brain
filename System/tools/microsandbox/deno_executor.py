# --- System/tools/microsandbox/deno_executor.py ---
import subprocess
from pathlib import Path
from typing import Dict, Any


def execute_sandboxed_js(
    script_path: Path, staging_dir: Path, timeout: int = 10
) -> Dict[str, Any]:
    """
    🛡️ Process-Level JS Sandbox: Executes code inside an embedded Deno process
    with zero external privileges and a strict file-system path lock.
    """
    if not script_path.exists():
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": f"Script not found: {script_path}",
        }

    # Enforce strict permission gates on the Deno runtime command invocation layer
    command = [
        "deno",
        "run",
        "--net=none",  # Complete network isolation
        f"--allow-read={staging_dir.resolve()}",  # Read access restricted to staging directory
        f"--allow-write={staging_dir.resolve()}",  # Write access restricted to staging directory
        str(script_path.resolve()),
    ]

    try:
        res = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(staging_dir.resolve()),
        )
        return {
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Execution halted: Time limit exceeded ({timeout}s).",
        }
