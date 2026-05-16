from System.core.paths import ROOT_DIR
import os
import yaml  # type: ignore
from litellm import completion  # type: ignore
from rich.console import Console

console = Console()

CONFIG_PATH = ROOT_DIR / "System" / "config" / "agents.yaml"


def filter_attention(prompt: str, raw_memory: str) -> str:
    """
    The Thalamus (Semantic Attention Filter).
    Reads the Neocortex memory and extracts ONLY the tokens relevant to the current task.
    """
    # 1. Biological Fast-Path: If the memory is small, don't waste time filtering it.
    if len(raw_memory) < 2000:
        return raw_memory

    console.print(
        "[dim magenta]🧠 Thalamus Active: Filtering context noise...[/dim magenta]"
    )

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Use the cheapest possible model for the subconscious filter
        model = config.get("models", {}).get("gpt_mini", "gpt-4o-mini")
        if os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            model = config.get("models", {}).get(
                "claude_haiku", "claude-3-haiku-20240307"
            )
    except Exception:
        model = "gpt-4o-mini"

    system_prompt = """You are the Thalamus of Brain OS.
Your job is to filter the long-term memory (Neocortex) and extract ONLY the exact bullet points, facts, and context highly relevant to the User's current task.
Do NOT rewrite the memory. Do NOT answer the prompt.
Just output the exact lines from the memory that are relevant.
If absolutely nothing in the memory is relevant to the task, output "No relevant context found."
Keep it as dense and short as possible."""

    try:
        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"USER TASK:\n{prompt}\n\nRAW MEMORY:\n{raw_memory}",
                },
            ],
            temperature=0.0,
        )
        filtered_memory = str(response.choices[0].message.content).strip()
        return f"--- FILTERED CONTEXT (THALAMUS) ---\n{filtered_memory}"

    except Exception as e:
        console.print(f"[dim red]Thalamus API Error. Bypassing filter. ({e})[/dim red]")
        # Structural fallback: just grab the most recent 4000 characters
        return raw_memory[-4000:]


def process_sensory_input(source: str, payload: str) -> str:
    """
    The Thalamic gateway for ascending sensory data from the Spine.
    Filters, prioritizes, and formats impulses before they reach the Prefrontal Cortex.
    """
    return f"<ascending_stimulus source='{source}'>\n{payload}\n</ascending_stimulus>"
