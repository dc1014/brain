# 🧠 Brain: The Life OS

![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-purple.svg)
![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)

Brain is an open-source "Second Brain" and semi-autonomous agent ecosystem. It bridges the gap between your local file system, unstructured thoughts, LLM reasoning engines, and MCP servers while being as safe as I can make it and minimizing token usage. Obsidian is used as the primary UI interface for viewing content in Brain, while Claude + MCP are how Brain acts. Brain is open, though, so bring your own "whatever."

Brain uses **Shift-Left Engineering** and **The Unix Philosophy** as a generalized principle. Everything is a file so you can see and change everything. It utilizes a deterministic router to bound the AI, pre-calculate execution tracks, and strictly sandbox file operations. It is designed to be fast, token-optimized, observable, highly secure, and completely open.

---

## 🌟 Core Philosophy
1. **Own Your Brain:** Your Brain and everything in it - data (Vault), journals, art, code, and business IP - is yours. All personal folders are `.gitignore`d.
2. **Zero-Waste Token Economics:** Context limits are respected. The system dynamically extracts payloads and drops intermediate reasoning steps to keep context loops lean.
3. **Open-Source & UNIX-Native:** Everything is a file. The routing system, API logic, memory structures, and prompts are 100% open-source and run entirely on your machine.

---

## 🏗️ Architecture

### 1. The Deterministic Router (Shift-Left Bouncer)
Before an expensive agent ever boots up, a high-speed Auditor model intercepts the prompt. It enforces hard security rules (e.g., blocking `rm` commands or access to system files) and calculates the **Intent Domain** and **Execution Route** (`FAST`, `READ_ONLY`, or `COMPLEX`).

### 2. Declarative Agent Pipelines
Unlike heavy frameworks with hardcoded agent logic, Brain is driven by a single, human-readable YAML file (`System/agents.yaml`). The Python engine handles the loops and tool executions, but the intelligence—who the agents are, what models they use, and how they hand off tasks—is completely declarative.

*(Note: Brain features a **Zero-Config Fallback**. Supply keys for Anthropic, Google, and OpenAI to use a full Trinity of specialized models, or supply just ONE key and the system will gracefully map all roles to that single API).*

### 3. Hierarchical Context Engineering
The OS dynamically stacks memory. It always injects `Meta/global-memory.md` (your core identity), but uses intent-mapping to selectively inject `Personal/`, `Professional/`, or `Studio/` memory based on the active task, saving massive amounts of tokens.

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python 3.12+**
* **[uv](https://github.com/astral-sh/uv):** The blazingly fast Python package manager.

### 1. Clone & Install
Clone the core engine and lock in the dependencies:
```bash
git clone [https://github.com/yourusername/brain.git](https://github.com/yourusername/brain.git)
cd brain
uv sync
```

### 2. Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```
Populate `.env` with your API keys. (You can start with just an `OPENAI_API_KEY` to test the system).

### 3. Vault Initialization
Because Brain is privacy-first, your personal data directories are ignored in git. Build your safe vault structure and foundational memory files instantly:
```bash
uv run System/router.py init
```

---

## 💻 Usage & Commands

Brain operates via a unified CLI router. 

### Execute a Task
The system will auto-route, assign domains, and spin up the necessary agents safely inside your vault.
```bash
uv run System/router.py task "Help me brainstorm a marketing plan for my project."
```

### View Telemetry & Logs
Brain logs every token, prompt, and action for perfect local observability.
```bash
uv run System/router.py logs --limit 3
```

### ⚡ Autonomous Execution & HITL (Forge)
Brain is capable of spawning and orchestrating other software engines (like `create-react-app` or autonomous builders like `Forge`).
Because letting an AI run terminal commands is dangerous, Brain enforces **Human-in-the-Loop (HITL)**. Before Brain executes a shell command on your behalf, it will pause the terminal and explicitly ask for your permission:
`Brain OS wants to run: 'python orchestrator.py'. Allow? (Y/n)`

### 🌙 The Sleep Cycle Compactor (Memory Synthesis)
At the end of the day, command the OS to sleep. The Auditor will read your daily `logs/agent_interactions.jsonl`, extract permanent high-value facts (strategies, preferences, coding rules), inject them directly into your Markdown memory files, and safely rotate/archive the logs.
```bash
uv run System/router.py sleep
```

---

## ⚙️ Customizing Agents & Pipelines

You never need to touch Python code to change how Brain thinks. Everything is controlled via `System/agents.yaml`.

**Swap Models Instantly:** Want to use local models or different providers? Just update the `models` block (LiteLLM supports 100+ providers, including Ollama):
```yaml
models:
  primary_worker: "anthropic/claude-3-5-haiku-latest"
  local_researcher: "ollama/llama3"
```

**Edit Prompts & Roles:** Rewrite the Bouncer's rules or the Engineer's system prompt in plain text:
```yaml
agents:
  engineer:
    name: "Engineer (Claude)"
    model: "primary_worker"
    system_prompt: |
      You are a highly structured system engineer...
```

**Compose Execution Pipelines:** Define exactly who runs, what tools they get, and what memory context they read during a route:
```yaml
routes:
  COMPLEX:
    - agent: "engineer"
      tools: ["base", "write"]
      context: ["Meta", "Domain", "Studio"]
    - agent: "auditor"
      tools: []
      context: ["Meta", "Domain"]
```

---

## 🛡️ Security & Sandboxing
The Worker agent is completely sandboxed. It can only execute explicit Python tools (`write_safe_file`, `read_safe_file`, `list_safe_directory`, `append_safe_file`) scoped strictly to your vault directories. Attempts to traverse directories (`../`), access `.env`, or write to the system kernel are mathematically blocked at the tool layer.

## 🏭 Forge: The Factory Floor
Brain OS acts as the Project Manager, but it delegates application builds to **Forge**—a deterministic, ATDD-driven React/Python template that lives in your `Studio/` directory.

### 1. Installing Forge
Brain OS manages the complete scaffolding and dependency hydration (Shift-Left) for new Forge projects. To spin up a new application:
```bash
uv run System/router.py task "Use bootstrap_project to create a new project called 'My-App' using the Forge template."
```
*Note: `bootstrap_project` automatically clones the repository, renames the remote to `upstream`, and runs `npm install` and `uv sync`.*

### 2. Updating Forge from Remote
Because Brain OS renames the original Forge repository remote to `upstream` during installation, you can easily pull the latest architectural updates from the master Forge template without overwriting your custom app code:
```bash
uv run System/router.py task "Run execute_command to 'git fetch upstream' and 'git merge upstream/main' inside Studio/My-App"
```

### 3. Prompting Forge (Ticket-Driven Delegation)
**Never play the "Telephone Game"** by passing dense, multi-step requirements directly into the `operate_forge` command prompt. Instead, use the real-world PM workflow: write a ticket, and tell the engineer to read the ticket.

**The Best-Practice Workflow:**
1. **Stage Assets:** Use Brain OS to move any images from `Media/` to the Forge `public/` directory.
2. **Write the Ticket:** Instruct Brain OS to write the requirements into `Studio/My-App/docs/product/current_run.md`.
3. **Dispatch the Worker:** Run `operate_forge` with a minimal instruction.

**Example CEO Command:**
> `COMPLEX TASK: Step 1. Overwrite Studio/My-App/docs/product/current_run.md. Write: "Target: src/web/components/Hero.tsx. Requirement: Add an img tag pointing to /logo.png and a GitHub CTA button." Step 2. Run operate_forge with: "[START: Engineering] Read current_run.md. Refactor the target file to perfectly match the requirement. Follow ATDD. Output ROUTING: [Ops]."`

*For overly complex refactors, use the "Payload Drop" method: Have Brain OS write the complete raw code to `docs/product/payload.txt`, and instruct Forge to simply copy-paste it into the target file.*

### 4. Debugging Forge (The Ghost in the Machine)
If Forge reports `Exit Code 0 (Success)` but your browser does not reflect the changes, **do not assume the system is broken.** You are likely experiencing AI Attention Collapse or a "Ghost File" (where the AI successfully wrote the code, but to a hallucinated/orphaned file path).

**The Debug Protocol:**
1. **Check Telemetry:** Open `Studio/My-App/docs/ops/telemetry.jsonl`. This file contains the exact, unedited JSON payload the AI executed.
2. **Verify Paths:** Check if the AI wrote to `src/web/Hero.tsx` instead of `src/web/components/Hero.tsx`.
3. **Check the Router:** Ensure the AI didn't accidentally update `main.tsx` to point to a dead file.
4. **Fix via Brain:** Instruct Brain OS to delete the orphaned files and fix the imports in your router.

## 🤝 Contributing
Contributions to the core routing engine and API layers are welcome. 
Please ensure all tests pass before submitting a PR:
```bash
uv run pytest System/tests/
uv run ruff check .
```

---
*Brain OS — Designed for humans to collaborate safely with AI.*