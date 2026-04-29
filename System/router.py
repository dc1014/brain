import argparse
from dotenv import load_dotenv
from litellm import completion

# Load the vault keys
load_dotenv()

# Define our specific agent models
ORCHESTRATOR = "gemini/gemini-2.5-flash"
WORKER = "anthropic/claude-haiku-4-5"
AUDITOR = "openai/gpt-4o-mini"


def run_agent(role_name, model_string, system_prompt, user_prompt):
    print(f"\n[{role_name}] is thinking...")
    try:
        response = completion(
            model=model_string,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    # Set up the CLI commands
    parser = argparse.ArgumentParser(description="Brain Router")
    parser.add_argument(
        "--task", type=str, required=True, help="The task you want the AI to perform."
    )
    args = parser.parse_args()

    print(f"🚀 Initializing Life OS task: '{args.task}'")

    # Step 1: Claude does the deep, structured work
    worker_system = "You are a highly structured system engineer. Break this task down into a clear, actionable step-by-step plan."
    claude_draft = run_agent("Worker (Claude)", WORKER, worker_system, args.task)

    print("\n--- CLAUDE'S DRAFT ---")
    print(claude_draft)

    # Step 2: Gemini (Me) reviews and orchestrates the final output
    orchestrator_system = "You are the central orchestrator of a Life OS. Review the worker's plan. Summarize it into a final, polished 3-bullet-point executive summary."
    final_output = run_agent(
        "Orchestrator (Gemini)", ORCHESTRATOR, orchestrator_system, claude_draft
    )

    print("\n--- FINAL ORCHESTRATION ---")
    print(final_output)


if __name__ == "__main__":
    main()
