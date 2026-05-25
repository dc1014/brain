import asyncio
import threading
import yaml  # type: ignore
import shlex
from litellm import acompletion  # type: ignore
from rich.console import Console
from System.core.paths import ROOT_DIR
from System.neuroanatomy.limbic.amygdala import scan_command

console = Console()

# ⚡ SHIFT-LEFT: Ensure path correctly points to System/config
CONFIG_PATH = ROOT_DIR / "System" / "config" / "agents.yaml"


async def trigger_immune_response_async(
    failed_cmd: str, stderr: str, cwd: str, max_retries: int = 1
) -> tuple[bool, str]:
    """Fully asynchronous immune response to prevent Latency Seizures."""
    console.print(
        "\n[bold yellow]🦠 Microglia Activated: Async Immune response triggered for failing command.[/bold yellow]"
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

        prompt = f"""You are the Microglia (Immune System) for CoreTex OS.
A shell command failed. Analyze the error and provide EXACTLY ONE shell command to fix it.
DO NOT provide markdown, explanations, or any other text. JUST the raw command.
Failed Command: `{failed_cmd}`
Error Log:
{current_stderr}"""

        try:
            # ⚡ Async LLM synthesis
            response = await acompletion(
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

        # ⚡ Execute the safe antibody asynchronously
        try:
            fix_args = shlex.split(antibody_cmd)
            fix_proc = await asyncio.create_subprocess_exec(
                *fix_args,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            # 🎯 RUFF FIX: Discard stdout, we only need stderr if it fails
            _, fix_stderr_bytes = await fix_proc.communicate()
            fix_stderr = fix_stderr_bytes.decode()
            fix_returncode = fix_proc.returncode
        except Exception as e:
            return False, f"Microglia execution failed: {str(e)}"

        if fix_returncode != 0:
            return False, f"Microglia antibody failed: {fix_stderr}"

        # ⚡ Retry original command asynchronously
        try:
            retry_args = shlex.split(failed_cmd)
            retry_proc = await asyncio.create_subprocess_exec(
                *retry_args,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            retry_stdout_bytes, retry_stderr_bytes = await retry_proc.communicate()
            retry_stdout = retry_stdout_bytes.decode()
            retry_stderr = retry_stderr_bytes.decode()
            retry_returncode = retry_proc.returncode
        except Exception as e:
            return False, f"Microglia retry execution failed: {str(e)}"

        if retry_returncode == 0:
            console.print(
                "[bold green]🦠 Microglia Successfully Healed the System.[/bold green]\n"
            )
            return (
                True,
                f"Microglia autonomously applied a patch (`{antibody_cmd}`) and retried successfully.\nSTDOUT:\n{retry_stdout}",
            )
        else:
            current_stderr = retry_stderr

    return False, f"Microglia exhausted max retries. Error:\n{current_stderr}"


def trigger_immune_response(
    failed_cmd: str, stderr: str, cwd: str, max_retries: int = 1
) -> tuple[bool, str]:
    """
    Synchronous wrapper for backward compatibility.
    Safely bridges the Motor Cortex's blocking calls to the new async Microglia.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 🎯 MYPY FIX: Strictly type the fallback result tuple
        result: tuple[bool, str] = (False, "Microglia thread execution failed.")

        def run_in_thread() -> None:
            nonlocal result
            result = asyncio.run(
                trigger_immune_response_async(failed_cmd, stderr, cwd, max_retries)
            )

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        return result
    else:
        return asyncio.run(
            trigger_immune_response_async(failed_cmd, stderr, cwd, max_retries)
        )
