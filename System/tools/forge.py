import json
import subprocess
import shutil
import os
from pathlib import Path
from rich.console import Console
from System.core.paths import ROOT_DIR
from .sandbox import is_safe_path
from System.core.schemas import ExecutionResult

console = Console()


def operate_forge(project_name: str, instruction: str) -> ExecutionResult:
    """Operates a Forge instance securely via handoff.md and returns its telemetry."""
    try:
        target_path: Path = (ROOT_DIR / "Studio" / project_name).resolve()

        if not is_safe_path(target_path, require_write=True):
            reason = (
                f"SECURITY BLOCK: Access denied. {target_path} is outside safe zones."
            )
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        orchestrator_path = target_path / "orchestrator.py"
        if not orchestrator_path.exists():
            reason = f"ERROR: Forge engine not found at {orchestrator_path.relative_to(ROOT_DIR)}."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        ops_dir = target_path / "docs" / "ops"
        ops_dir.mkdir(parents=True, exist_ok=True)
        handoff_path = ops_dir / "handoff.md"
        handoff_path.write_text(f"PROMPT: {instruction}\n", encoding="utf-8")

        console.print(
            "\n[bold red]⚠️  SECURITY ALERT: FORGE OPERATION REQUESTED[/bold red]"
        )
        console.print(
            f"[yellow]Brain OS wants to command Forge for project:[/yellow] '{project_name}'\n[yellow]Instruction:[/yellow] '{instruction}'"
        )

        if os.environ.get("BRAIN_OS_HEADLESS") == "1":
            user_input = "y"
        else:
            try:
                user_input = input("Allow execution? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                user_input = "n"

        if user_input not in ["y", "yes"]:
            reason = "SECURITY BLOCK: User explicitly denied Forge operation."
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        console.print(f"[dim]Booting Forge engine for '{project_name}'...[/dim]\n")

        from System.neuroanatomy.systemic.blood_brain_barrier import wrap_with_apoptosis

        membrane_script = wrap_with_apoptosis(str(orchestrator_path))

        result = subprocess.run(
            ["uv", "run", membrane_script],
            cwd=str(target_path),
            capture_output=True,
            text=True,
        )

        telemetry_path = ops_dir / "telemetry.jsonl"
        telemetry_data = "No telemetry emitted."
        if telemetry_path.exists():
            with open(telemetry_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    try:
                        t_json = json.loads(lines[-1])
                        telemetry_data = f"Last Agent: {t_json.get('agent')} | Tokens: {t_json.get('prompt_tokens')} | Latency: {t_json.get('latency_s')}s"
                    except json.JSONDecodeError:
                        telemetry_data = "Telemetry parsing failed."

        handoff_status = (
            handoff_path.read_text(encoding="utf-8").strip()
            if handoff_path.exists()
            else "No state."
        )

        summary = (
            f"FORGE EXECUTION COMPLETE (Exit Code {result.returncode})\n\n"
            f"--- TELEMETRY ---\n{telemetry_data}\n\n"
            f"--- HANDOFF STATE ---\n{handoff_status}\n\n"
            f"--- ENGINE STDOUT ---\n(Streamed live to user terminal. Rely on Telemetry and Handoff State above.)\n"
        )

        if result.returncode != 0:
            summary += "\n--- ERROR ---\nForge execution failed. Please check the live terminal output for the exact stack trace."
            return ExecutionResult(
                success=False,
                output=summary,
                block_reason="Forge execution returned a non-zero exit code.",
            )

        return ExecutionResult(success=True, output=summary)

    except Exception as e:
        reason = f"ERROR: Failed to operate Forge - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)


def bootstrap_project(
    project_name: str, template_url: str = "https://github.com/mrdanielcasper/forge.git"
) -> ExecutionResult:
    """Clones a project archetype into the Studio directory and initializes dependencies."""
    try:
        target_path: Path = (ROOT_DIR / "Studio" / project_name).resolve()
        if not is_safe_path(target_path, require_write=True):
            reason = f"SECURITY BLOCK: Access denied to clone into {target_path}."
            return ExecutionResult(success=False, output=reason, block_reason=reason)
        if target_path.exists():
            reason = f"ERROR: Directory exists at {target_path.relative_to(ROOT_DIR)}"
            return ExecutionResult(success=False, output=reason, block_reason=reason)

        result = subprocess.run(
            ["git", "clone", template_url, str(target_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            subprocess.run(
                ["git", "remote", "rename", "origin", "upstream"], cwd=str(target_path)
            )

            env_example = target_path / ".env.example"
            env_target = target_path / ".env"
            if env_example.exists() and not env_target.exists():
                env_target.write_text(
                    env_example.read_text(encoding="utf-8"), encoding="utf-8"
                )

            console.print(f"[dim]Hydrating dependencies for {project_name}...[/dim]")

            npm_path = shutil.which("npm")
            uv_path = shutil.which("uv")

            if uv_path:
                subprocess.run(
                    [uv_path, "sync"], cwd=str(target_path), capture_output=True
                )
            if npm_path:
                subprocess.run(
                    [npm_path, "install"], cwd=str(target_path), capture_output=True
                )

            return ExecutionResult(
                success=True,
                output=f"SUCCESS: Bootstrapped and hydrated at {target_path.relative_to(ROOT_DIR)}",
            )

        reason = f"ERROR: Git clone failed - {result.stderr}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)
    except Exception as e:
        reason = f"ERROR: Failed to bootstrap project - {str(e)}"
        return ExecutionResult(success=False, output=reason, block_reason=reason)
