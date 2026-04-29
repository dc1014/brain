import os
from dotenv import load_dotenv
from litellm import completion

# Securely load the API keys from your .env file
load_dotenv()

# We use the fastest, cheapest models for a quick ping
agents = {
    "Orchestrator (Gemini)": "gemini/gemini-2.5-flash",
    "Worker (Claude)": "anthropic/claude-haiku-4-5",
    "Auditor (ChatGPT)": "openai/gpt-4o-mini"
}

print("🧠 Initiating Life OS Smoke Test...\n" + "-"*40)

for role, model in agents.items():
    print(f"Pinging {role} via {model}...")
    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": "Acknowledge connection. Respond with exactly: 'Status Green'."}],
            max_tokens=10
        )
        print(f"✅ Success: {response.choices[0].message.content}\n")
    except Exception as e:
        print(f"❌ Failed: {e}\n")

print("-" * 40 + "\nTest Complete.")