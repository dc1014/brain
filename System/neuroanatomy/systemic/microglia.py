from System.core.paths import ROOT_DIR
import subprocess
import yaml  # type: ignore
import shlex
from litellm import completion  # type: ignore
from rich.console import Console
from System.neuroanatomy.limbic.amygdala import scan_command

console = Console()

CONFIG_PATH = ROOT_DIR / "System" / "config" / "agents.yaml"


def trigger_immune_response(
    failed_cmd: str, stderr: str, cwd: str, max_retries: int = 1
) -> tuple[bool, str]:
    console.print(
        "\n[bold yellow]🦠 Microglia Activated: Immune response triggered for failing command.[/bold yellow]"
    )

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        model = config.get("models", {}).get("gpt_mini", "gpt-4o-mini")
    except Exception:
        model = "gpt-4o-mini"

    current_attempt = 0
    current_stderr = stderr

    while current_attempt < max_retries:
        current_attempt += 1

        prompt = f"""You are the Microglia (Immune System) for Brain OS.
A shell command failed. Analyze the error and provide EXACTLY ONE shell command to fix it.
DO NOT provide markdown, explanations, or any other text. JUST the raw command.
Failed Command: `{failed_cmd}`
Error Log:
{current_stderr}"""

        try:
            response = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            antibody_cmd = str(response.choices[0].message.content).strip()
            if antibody_cmd.startswith("```"):
                antibody_cmd = (
                    antibody_cmd.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                )
        except Exception as e:
            return False, f"LLM synthesis failed: {str(e)}"

        console.print(
            f"[bold green]💉 Microglia synthesized antibody: `{antibody_cmd}`[/bold green]"
        )

        # SECURE: Ensure the LLM didn't hallucinate a dangerous command
        is_safe, cmd_reason = scan_command(antibody_cmd)
        if not is_safe:
            return (
                False,
                f"Microglia generated unsafe command blocked by Amygdala: {cmd_reason}",
            )

        # Execute the safe antibody
        try:
            fix_args = shlex.split(antibody_cmd)
            fix_result = subprocess.run(
                fix_args, cwd=cwd, capture_output=True, text=True, shell=False
            )
        except Exception as e:
            return False, f"Microglia execution failed: {str(e)}"

        if fix_result.returncode != 0:
            return False, f"Microglia antibody failed: {fix_result.stderr}"

        # Retry original command
        try:
            retry_args = shlex.split(failed_cmd)
            retry_result = subprocess.run(
                retry_args, cwd=cwd, capture_output=True, text=True, shell=False
            )
        except Exception as e:
            return False, f"Microglia retry execution failed: {str(e)}"

        if retry_result.returncode == 0:
            console.print(
                "[bold green]🦠 Microglia Successfully Healed the System.[/bold green]\n"
            )
            return (
                True,
                f"Microglia autonomously applied a patch (`{antibody_cmd}`) and retried successfully.\nSTDOUT:\n{retry_result.stdout}",
            )
        else:
            current_stderr = retry_result.stderr

    return False, f"Microglia exhausted max retries. Error:\n{current_stderr}"
