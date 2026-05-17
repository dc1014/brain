import os
import yaml  # type: ignore
from pathlib import Path
from rich.console import Console
from litellm import completion  # type: ignore

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = ROOT_DIR / "System" / "config" / "agents.yaml"
MUTATIONS_PATH = ROOT_DIR / "Meta" / "Mutations.md"


def observe_human_behavior(project_name: str) -> None:
    """
    Mirror Neurons: Scans a user's project to deduce their coding style,
    and proposes genetic mutations to align the AI's output with the human's preferences.
    """
    target_dir = (ROOT_DIR / "Studio" / project_name).resolve()

    if not target_dir.exists():
        console.print(
            f"[bold red]🛑 Cannot observe '{project_name}'. Directory not found.[/bold red]"
        )
        return

    console.print(
        f"\n[bold magenta]👁️  Activating Mirror Neurons: Observing human code in '{project_name}'...[/bold magenta]"
    )

    # 1. Gather a sample of human code (Ignore massive files or generated folders)
    valid_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}
    ignore_dirs = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}

    sampled_code = ""
    files_read = 0

    for filepath in target_dir.rglob("*"):
        if filepath.is_file() and filepath.suffix in valid_exts:
            if any(ignored in filepath.parts for ignored in ignore_dirs):
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
                # Take a generous sample of each file
                sampled_code += f"\n--- FILE: {filepath.relative_to(target_dir)} ---\n{content[:1500]}\n"
                files_read += 1
                if files_read >= 10:  # Cap at 10 files to save tokens
                    break
            except Exception:
                continue

    if not sampled_code:
        console.print("[dim]No valid code files found to observe.[/dim]")
        return

    # 2. Trigger the Subconscious Analysis
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        model = config.get("models", {}).get("gpt_mini", "gpt-4o-mini")
        if os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            model = config.get("models", {}).get(
                "claude_haiku", "claude-3-haiku-20240307"
            )
    except Exception:
        model = "gpt-4o-mini"

    system_prompt = """You are the Mirror Neurons of Brain OS.
Your job is biological imitation and developer empathy.
Analyze the provided human-written code sample. Identify their distinct coding style, including:
- Variable naming conventions (camelCase, snake_case, etc.)
- Commenting style (JSDoc, inline, sparse, dense)
- Structural preferences (arrow functions vs standard, class-based vs functional)
- Import structures and spacing

Synthesize these observations into a strict, concise style guide.
OUTPUT FORMAT: You MUST output exactly two <neuroplasticity> tags—one for the product_manager and one for the qa_auditor—so they adopt this style permanently.
Example:
<neuroplasticity agent="product_manager">MIRROR NEURON ALIGNMENT: Always write React components using const arrow functions, enforce strict TypeScript interfaces, and use 2-space indentation.</neuroplasticity>"""

    try:
        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"HUMAN CODE SAMPLE:\n{sampled_code}"},
            ],
        )
        raw_output = str(response.choices[0].message.content)

        # 3. Stage the Mutations (Cortical Inhibition)
        import re

        np_matches = list(
            re.finditer(
                r'<neuroplasticity agent="(.*?)">(.*?)</neuroplasticity>',
                raw_output,
                re.DOTALL,
            )
        )

        if np_matches:
            MUTATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(MUTATIONS_PATH, "a", encoding="utf-8") as f:
                for match in np_matches:
                    f.write(f"\n{match.group(0)}\n")

            console.print(
                "[bold green]✨ Mirror Neurons successfully extracted human coding style![/bold green]"
            )
            console.print(
                f"[bold yellow]🧬 {len(np_matches)} new genetic mutation(s) proposed! Review Meta/Mutations.md before running 'brain evolve'.[/bold yellow]"
            )
        else:
            console.print(
                "[dim]Mirror Neurons analyzed the code but found no distinct patterns to mimic.[/dim]"
            )

    except Exception as e:
        console.print(f"[bold red]🛑 Mirror Neuron Failure: {e}[/bold red]")
