import os
from litellm import completion


def evaluate_cognitive_output(actual_output: str, grading_rubric: str) -> bool:
    """
    Acts as a strict LLM-as-a-Judge to evaluate non-deterministic text outputs.
    Returns True if the output passes the rubric, False otherwise.
    """
    # Prefer Gemini for fast, cheap evals, but fallback to OpenAI if needed
    model = (
        "gemini/gemini-2.5-flash"
        if os.environ.get("GEMINI_API_KEY")
        else "openai/gpt-4o-mini"
    )

    prompt = (
        "You are a strict, automated Continuous Integration evaluator for CoreTex OS.\n"
        "Your only job is to evaluate if the ACTUAL_OUTPUT passes the GRADING_RUBRIC.\n\n"
        f"--- GRADING RUBRIC ---\n{grading_rubric}\n\n"
        f"--- ACTUAL OUTPUT ---\n{actual_output}\n\n"
        "If it passes, output EXACTLY the word: PASS\n"
        "If it fails, output EXACTLY the word: FAIL"
    )

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # Zero variance for strict evaluations
        )
        grade = str(response.choices[0].message.content).strip().upper()
        return "PASS" in grade
    except Exception as e:
        print(f"Eval Harness Failure: {e}")
        return False
