# --- System/tests/integrations/test_eval_daydream.py ---
import asyncio
import os
import pytest

from System.core.paths import ROOT_DIR
from System.neuroanatomy.autonomic.dmn import trigger_daydreams
from System.llm import run_agent_async


# ⚡ THE FIX: Makes the eval strictly optional so it doesn't break parallel CI runs!
@pytest.mark.skipif(
    os.environ.get("RUN_EVALS") != "1",
    reason="Expensive LLM Eval. Run with RUN_EVALS=1 to execute.",
)
def test_daydream_cognitive_quality():
    """
    LLM-as-a-Judge Evaluation Harness for the Default Mode Network.
    Tests if the Daydreamer actually synthesizes deep strategic insights.
    """
    daydreams_file = ROOT_DIR / "Meta" / "DMN" / "daydreams.md"

    # 1. Capture the initial state of the ledger
    initial_content = (
        daydreams_file.read_text(encoding="utf-8") if daydreams_file.exists() else ""
    )

    print("\n\n[EVAL] Triggering targeted Daydream sequence...")

    # 2. Trigger the DMN with a highly specific, complex engineering scenario
    test_scenario = "Refactoring the internal Pytest Orchestration Suite to handle asynchronous LLM API rate limits."
    trigger_daydreams(topic=test_scenario, domain="META")

    # 3. Extract the new Epiphany appended to the file
    new_content = daydreams_file.read_text(encoding="utf-8")
    epiphany_text = new_content.replace(initial_content, "").strip()

    print(f"\n[EVAL] Extracted New Epiphany:\n{epiphany_text}\n")

    # Basic deterministic assertions
    assert epiphany_text != "", (
        "EVAL FAIL: The Daydreamer failed to append any text to the file."
    )
    assert "## Epiphany" in epiphany_text, (
        "EVAL FAIL: Missing the required '## Epiphany' Markdown header."
    )

    # 4. LLM-as-a-Judge (GPT-4o)
    print("[EVAL] Booting GPT-4o Judge to evaluate cognitive quality...")
    judge_prompt = f"""
    You are an expert Principal Staff Engineer and AI Evaluator.
    You are grading a background agent's 'Daydream' (a strategic synthesis of system state).

    SCENARIO GIVEN TO THE AGENT:
    "{test_scenario}"

    AGENT'S OUTPUT:
    {epiphany_text}

    RUBRIC:
    1. **Formatting**: Does it contain clean markdown, paragraph breaks, and lists? (No giant unformatted text blobs).
    2. **Insight Quality**: Does it offer a novel engineering connection, architectural pattern, or deep structural thought? (It MUST NOT just repeat the scenario back to the user).
    3. **Actionability**: Does it suggest a tangible path forward?

    Output EXACTLY 'PASS' if it meets all criteria perfectly.
    If it fails ANY criteria, output 'FAIL' followed by a detailed critique of why the agent's logic or formatting was poor.
    """

    evaluation = asyncio.run(
        run_agent_async(
            role_name="Eval_Judge",
            system_prompt="You are a strict, uncompromising evaluation judge.",
            user_prompt=judge_prompt,
            model_string="openai/gpt-4o",  # Use standard GPT-4o for high-reasoning evaluation
        )
    )

    print(f"\n[EVAL JUDGE OUTPUT]\n{evaluation.text}\n")

    # 5. Final Assertion
    assert "PASS" in evaluation.text.upper(), (
        f"Daydream Quality Eval Failed: {evaluation.text}"
    )
