import subprocess
import yaml  # type: ignore
import os
from pathlib import Path
from litellm import completion  # type: ignore
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "System" / "config" / "agents.yaml"


def trigger_immune_response(
    failed_cmd: str, stderr: str, cwd: str, max_retries: int = 1
) -> tuple[bool, str]:
    """
    The Microglia (Autonomous Bug Fixing).
    Intercepts failed shell commands and attempts to heal the environment or fix the code
    before returning the failure to the higher-order executive agents.
    """
    console.print(
        "\n[bold yellow]🦠 Microglia Activated: Immune response triggered for failing command.[/bold yellow]"
    )

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 1. Biological Downgrade: Use the cheapest, fastest heuristic model for immune responses
        model = config.get("models", {}).get("gpt_mini", "gpt-4o-mini")
        if os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            model = config.get("models", {}).get(
                "claude_haiku", "claude-3-haiku-20240307"
            )

    except Exception:
        model = "gpt-4o-mini"  # Fallback

    current_attempt = 0
    current_stderr = stderr

    while current_attempt < max_retries:
        current_attempt += 1

        # 2. Diagnose and generate a targeted antibody (patch command)
        prompt = f"""You are the Microglia (Immune System) for Brain OS.
A shell command failed. Analyze the error and provide EXACTLY ONE shell command to fix it.
DO NOT provide markdown, markdown blocks, explanations, or any other text. JUST the raw command.
If it's a missing pip package, output the pip install command.
If it's a syntax error in a script, output a fast python -c script or sed command to rewrite the broken line.

Failed Command: `{failed_cmd}`
Working Directory: `{cwd}`
Error Traceback:
{current_stderr}
"""
        try:
            response = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            antibody_cmd = (
                str(response.choices[0].message.content).strip().replace("`", "")
            )

            if not antibody_cmd:
                return (
                    False,
                    f"Microglia failed to generate an antibody. Original Error:\n{current_stderr}",
                )

            console.print(
                f"[dim yellow]↳ Synthesizing Antibody: {antibody_cmd}[/dim yellow]"
            )

            # 3. Apply the antibody (execute the fix)
            fix_result = subprocess.run(
                antibody_cmd, cwd=cwd, capture_output=True, text=True, shell=True
            )
            if fix_result.returncode != 0:
                # The fix failed, abort immune response
                return (
                    False,
                    f"Microglia antibody failed: {fix_result.stderr}\nOriginal Error:\n{current_stderr}",
                )

            console.print(
                "[dim green]↳ Antibody successful. Retrying original command...[/dim green]"
            )

            # 4. Retry the original command
            retry_result = subprocess.run(
                failed_cmd, cwd=cwd, capture_output=True, text=True, shell=True
            )

            if retry_result.returncode == 0:
                console.print(
                    "[bold green]🦠 Microglia Successfully Healed the System.[/bold green]\n"
                )
                return (
                    True,
                    f"Microglia (Immune System) detected an error, applied a patch autonomously, and retried successfully.\nOutput:\n{retry_result.stdout}",
                )
            else:
                current_stderr = retry_result.stderr

        except Exception as e:
            return (
                False,
                f"Microglia API/Execution crash: {str(e)}\nOriginal Error:\n{current_stderr}",
            )

    return (
        False,
        f"Microglia exhausted max retries. The error persists:\n{current_stderr}",
    )
