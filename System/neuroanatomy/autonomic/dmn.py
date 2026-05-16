import subprocess
import time
import random
from pathlib import Path
from datetime import datetime
from rich.console import Console
from litellm import completion  # type: ignore

from System.core.paths import ROOT_DIR
from System.core.locks import BiologicalLock
from System.runtime import AGENT_CONFIG

console = Console()


def generate_dream_branch_name() -> str:
    """Generates a timestamped branch name for the dream state."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"dream/hypothesis_{timestamp}"


def _get_current_branch(target_dir: Path) -> str:
    """Identifies the current active branch before sleep."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return "main"


def enforce_rem_paralysis(project_name: str) -> tuple[str | None, str | None]:
    """
    Traps the AI in an isolated Git branch before it starts writing code.
    Returns (dream_branch_name, original_branch_name) if successful.
    """
    target_dir = ROOT_DIR / "Studio" / project_name

    if not target_dir.exists():
        console.print(
            f"[bold red]Cannot dream in {project_name}. Directory not found.[/bold red]"
        )
        return None, None

    is_repo = subprocess.run(
        ["git", "status"], cwd=str(target_dir), capture_output=True
    )
    if is_repo.returncode != 0:
        console.print(
            f"[bold red]Cannot induce REM paralysis: {project_name} is not a git repository.[/bold red]"
        )
        return None, None

    original_branch = _get_current_branch(target_dir)
    dream_branch = generate_dream_branch_name()

    console.print(
        f"[bold blue]💤 Inducing REM Paralysis. Shifting to isolated dream state: {dream_branch}[/bold blue]"
    )
    subprocess.run(
        ["git", "checkout", "-b", dream_branch],
        cwd=str(target_dir),
        capture_output=True,
    )

    return dream_branch, original_branch


def wake_from_rem(project_name: str, dream_branch: str, original_branch: str) -> None:
    target_dir = ROOT_DIR / "Studio" / project_name
    if not target_dir.exists():
        return

    console.print(
        "[bold yellow]☀️ Waking from REM sleep. Consolidating dream state...[/bold yellow]"
    )
    subprocess.run(["git", "add", "."], cwd=str(target_dir), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"Autonomic Dream Sequence: {dream_branch}"],
        cwd=str(target_dir),
        capture_output=True,
    )
    res = subprocess.run(
        ["git", "checkout", original_branch],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
    )

    if res.returncode == 0:
        console.print(
            f"[bold green]✨ Reality Restored. Active branch is back to '{original_branch}'. The dream is saved in '{dream_branch}'.[/bold green]"
        )
    else:
        console.print(
            f"[bold red]⚠️ Wake Error: Failed to restore branch '{original_branch}'. {res.stderr}[/bold red]"
        )


def _gather_dream_context() -> str:
    """Forages for random memories, recent errors, and code snippets to form a dream context."""
    context_parts = []

    log_path = ROOT_DIR / "System" / "logs" / "medulla.log"
    if log_path.exists():
        with BiologicalLock(str(log_path)):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                if lines:
                    context_parts.append(
                        "RECENT AUTONOMIC LOGS:\n" + "".join(lines[-20:])
                    )

    vault_dirs = [ROOT_DIR / "Personal", ROOT_DIR / "Studio", ROOT_DIR / "Meta"]
    all_md_files = []
    for d in vault_dirs:
        if d.exists():
            all_md_files.extend(list(d.rglob("*.md")))

    if all_md_files:
        chosen_files = random.sample(all_md_files, min(3, len(all_md_files)))
        for random_file in chosen_files:
            with BiologicalLock(str(random_file)):
                with open(random_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    context_parts.append(
                        f"MEMORY ENGRAM ({random_file.name}):\n{content[:1000]}"
                    )

    return "\n\n---\n\n".join(context_parts)


def trigger_daydreams() -> str:
    """
    The Default Mode Network entry point for sleep cycles.
    Invoked by the Pineal Gland during idle periods.
    """
    console.print(
        "\n[dim magenta]🧠 DMN: Scanning for projects to optimize during REM sleep...[/dim magenta]"
    )

    dream_context = _gather_dream_context()
    if not dream_context.strip():
        return "No context available for daydreaming."

    prompt = (
        "You are the Default Mode Network (DMN) of Brain OS. The system is asleep. "
        "Form a novel connection or suggest a codebase refactor based on these recent memories and errors.\n\n"
        f"DREAM CONTEXT:\n{dream_context}\n\n"
        "Format your response as a concise Markdown note."
    )

    try:
        model_name = AGENT_CONFIG.get("models", {}).get(
            "fast", "gemini/gemini-2.5-flash"
        )

        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        epiphany = response.choices[0].message.content

        daydream_dir = ROOT_DIR / "Meta" / "DMN"
        daydream_dir.mkdir(parents=True, exist_ok=True)
        daydream_file = daydream_dir / "daydreams.md"

        with BiologicalLock(str(daydream_file)):
            with open(daydream_file, "a", encoding="utf-8") as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n## 🌌 Epiphany ({timestamp})\n{epiphany}\n\n---\n")

        console.print(
            f"[dim purple]✨ DMN: Epiphany consolidated into {daydream_file.relative_to(ROOT_DIR)}[/dim purple]"
        )
        return "Daydream cycle completed successfully."
    except Exception as e:
        console.print(f"[bold red]❌ DMN Nightmare: {str(e)}[/bold red]")
        return f"Nightmare: {str(e)}"
