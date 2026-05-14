import os
import yaml  # type: ignore
from pathlib import Path
from rich.console import Console
from litellm import completion  # type: ignore

# --- SHIFT-LEFT: Global Import ---
from System.tools import is_safe_path

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent.parent.resolve()
CONFIG_PATH = ROOT_DIR / "System" / "config" / "agents.yaml"
MUTATIONS_PATH = ROOT_DIR / "Meta" / "Mutations.md"


def observe_human_behavior(target: str, is_writing: bool = False) -> None:
    """
    Mirror Neurons: Scans human code or prose to deduce style,
    and proposes genetic mutations to align the AI's output.
    """

    target_path = (ROOT_DIR / target).resolve()

    # 1. SHIFT-LEFT SECURITY: Sandbox check
    if not is_safe_path(target_path):
        console.print(
            f"[bold red]🛑 SECURITY BLOCK: Cannot observe '{target}'. Outside safe zones.[/bold red]"
        )
        return

    if not target_path.exists():
        console.print(
            f"[bold red]🛑 Cannot observe '{target}'. Target not found.[/bold red]"
        )
        return

    console.print(
        f"\n[bold magenta]👁️  Activating Mirror Neurons: Observing human behavior in '{target_path.name}'...[/bold magenta]"
    )

    sampled_content = ""

    # 2. BEHAVIORAL GATHERING
    if is_writing:
        # GUARDRAIL 1: Explicit Targeted File Only
        if not target_path.is_file():
            console.print(
                "[bold red]🛑 For writing observation, you must provide a specific file path, not a directory.[/bold red]"
            )
            return
        sampled_content = f"--- WRITING SAMPLE: {target_path.name} ---\n{target_path.read_text(encoding='utf-8')[:3000]}"
    else:
        # Code observation (folder scanning)
        valid_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".md"}
        ignore_dirs = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
        files_read = 0

        for filepath in target_path.rglob("*"):
            if filepath.is_file() and filepath.suffix in valid_exts:
                if any(ignored in filepath.parts for ignored in ignore_dirs):
                    continue
                try:
                    content = filepath.read_text(encoding="utf-8")
                    sampled_content += f"\n--- FILE: {filepath.relative_to(target_path)} ---\n{content[:1500]}\n"
                    files_read += 1
                    if files_read >= 10:
                        break
                except Exception:
                    continue

    if not sampled_content:
        console.print("[dim]No valid content found to observe.[/dim]")
        return

    # 3. CONTEXTUAL PROMPTING
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

    if is_writing:
        # GUARDRAIL 2: Semantic Amnesia (Strict Content Stripping)
        system_prompt = """You are the Mirror Neurons of Brain OS. Your job is stylistic mimicry.
Analyze the provided human-written prose.
CRITICAL SAFETY INSTRUCTION: You MUST NOT extract, record, or mention ANY factual information, names, locations, secrets, PII, or subjects discussed in the text.
You are ONLY allowed to extract abstract structural patterns:
- Tone (formal, casual, empathetic, direct)
- Formatting habits (heavy use of bolding, bullet points, headers, emojis)
- Cadence (short punchy sentences vs long descriptive paragraphs)
- Lexicon (academic, conversational, technical)

Synthesize these abstract observations into a strict style guide.
OUTPUT FORMAT: Output <neuroplasticity agent="dispatcher"> and <neuroplasticity agent="product_manager"> tags.
Example: <neuroplasticity agent="dispatcher">MIRROR NEURON ALIGNMENT (WRITING): Always use a direct, punchy tone. Use bold text to emphasize key verbs. Never use emojis.</neuroplasticity>"""
    else:
        system_prompt = """You are the Mirror Neurons of Brain OS. Your job is biological imitation.
Analyze the human-written code. Identify their distinct coding style (variables, comments, structure).
Synthesize into a strict style guide.
OUTPUT FORMAT: Output <neuroplasticity agent="product_manager"> and <neuroplasticity agent="qa_auditor"> tags.
Example: <neuroplasticity agent="product_manager">MIRROR NEURON ALIGNMENT (CODE): Always use arrow functions and 2-space indents.</neuroplasticity>"""

    # 4. MUTATION
    try:
        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"HUMAN SAMPLE:\n{sampled_content}"},
            ],
        )
        raw_output = str(response.choices[0].message.content)

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
                "[bold green]✨ Mirror Neurons successfully extracted human abstract style![/bold green]"
            )
            console.print(
                f"[bold yellow]🧬 {len(np_matches)} new genetic mutation(s) proposed! Review Meta/Mutations.md.[/bold yellow]"
            )
        else:
            console.print(
                "[dim]Mirror Neurons analyzed the sample but found no distinct patterns to mimic.[/dim]"
            )

    except Exception as e:
        console.print(f"[bold red]🛑 Mirror Neuron Failure: {e}[/bold red]")
