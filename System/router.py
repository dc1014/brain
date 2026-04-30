import argparse
from dotenv import load_dotenv
from litellm import completion  # type: ignore

# Load the vault keys
load_dotenv()

# Define our specific agent models
ORCHESTRATOR: str = "gemini/gemini-2.5-flash"
WORKER: str = "anthropic/claude-haiku-4-5"
AUDITOR: str = "openai/gpt-4o-mini"


def run_agent(
    role_name: str, model_string: str, system_prompt: str, user_prompt: str
) -> str:
    print(f"\n[{role_name}] is thinking...")
    try:
        response = completion(
            model=model_string,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return str(response.choices[0].message.content)
    except Exception as e:
        return f"Error: {str(e)}"


def main() -> None:
    # Set up the CLI commands
    parser = argparse.ArgumentParser(description="Life OS Multi-Agent Router")
    parser.add_argument(
        "--task", type=str, required=True, help="The task you want the AI to perform."
    )
    args = parser.parse_args()

    print(f"🚀 Initializing Life OS task: '{args.task}'")

    # Step 1: Claude does the deep, structured work
    worker_system: str = "You are a highly structured system engineer. Break this task down into a clear, actionable step-by-step plan."
    claude_draft: str = run_agent("Worker (Claude)", WORKER, worker_system, args.task)

    print("\n--- CLAUDE'S DRAFT ---")
    print(claude_draft)

    # Step 2: Gemini (Me) reviews and orchestrates the final output
    orchestrator_system: str = "You are the central orchestrator of a Life OS. Review the worker's plan. Summarize it into a final, polished 3-bullet-point executive summary."
    final_output: str = run_agent(
        "Orchestrator (Gemini)", ORCHESTRATOR, orchestrator_system, claude_draft
    )

    print("\n--- FINAL ORCHESTRATION ---")
    print(final_output)


if __name__ == "__main__":
    main()
