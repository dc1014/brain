# 🧠 Brain: The Multi-Agent Life OS

![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-purple.svg)
![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)

Brain is an open-source "Second Brain" and semi-autonomous agent ecosystem. Think of it as the child of Open Claw and the "Second Brain" Obsidian + Claude setup everyone raves about (while adding Windows + Gemini + ChatGPT support). It bridges the gap between your local file system, unstructured thoughts, LLM reasoning engines, and MCP servers while being as safe as technically possible and minimizing token usage.

Obsidian serves as the primary UI "glass pane" for viewing and queuing content, while Python, Claude, ChatGPT, and Gemini act as the autonomous engine. Brain is completely open, though, so bring your own "whatever."

---

## 🌟 Core Philosophy

1. **Own Your Brain:** Your Brain and everything in it—data (Vault), journals, art, code, and business IP—is yours. The system operates strictly on local markdown files. All personal folders are `.gitignore`d.
2. **Shift-Left Security:** We catch errors, enforce routing, and demand human approval *before* execution. Agents can see everything but can only act within explicitly whitelisted sandboxes.
3. **The Unix Philosophy:** Everything is a file. Brain acts as the parent orchestrator but delegates software compilation and linting to the sub-projects inside `Studio/`.
4. **Zero-Waste Token Economics:** Context limits are respected. The system uses a deterministic router to wake up the cheapest, fastest model for simple tasks, saving the heavy reasoning models for complex software architecture.

---

## 🏗️ Architecture & Routing

### 1. The Deterministic Router (The Bouncer)
Before an expensive agent ever boots up, a high-speed Dispatcher model intercepts the prompt. It enforces hard security rules and calculates the **Intent Domain** and **Execution Route**:
* ⚡ **FAST:** Simple questions. No tools needed. (Gemini Flash)
* 📖 **READ_ONLY:** System searches and context aggregation. No file edits.
* 🗄️ **WORKSPACE:** Vault management. The `Archivist` agent searches, creates, and appends to Markdown files across the `Personal/`, `Professional/`, and `Studio/` domains. (GPT-4o-Mini)
* 🏭 **FORGE:** Software engineering. Wakes up the `Architect`, `Auditor`, and `Ops` pipeline to write code, stub ASTs, and securely execute shell commands in sub-directories. (Claude 3.5 Sonnet)

### 2. Declarative Agent Pipelines
Unlike heavy frameworks with hardcoded agent logic, Brain is driven by a single, human-readable YAML file (`System/config/agents.yaml`). The Python engine handles the loops and tool executions, but the intelligence—who the agents are, what models they use, and how they hand off tasks—is completely declarative.

### 3. Hierarchical Context Engineering
The OS dynamically stacks memory. It always injects `Meta/global-memory.md` (your core identity), but uses intent-mapping to selectively inject `Personal/`, `Professional/`, or `Studio/` memory based on the active task, saving massive amounts of tokens.

---

## 🛡️ Security & The Handoff Protocol

Brain uses a decoupled **Handoff Protocol** to keep you safe from autonomous shell scripts or recursive file deletions.

1. **Obsidian-Native Queue:** You send tasks to the AI via an Obsidian hotkey. Instead of executing immediately, Brain queues the task in a Markdown file (`System/Pending_Actions.md`).
2. **Human-In-The-Loop (HITL):** You review the proposed actions in plaintext.
3. **Headless Execution:** If approved, you trigger a second hotkey. The OS reads the queue, temporarily bypasses terminal execution blocks, runs the operations sequentially, and wipes the queue clean.
4. **ADR Immutability:** Architectural Decision Records (`adr/`) are locked at the file-system level. The AI cannot modify or move them without manual human override.

---

## 🚀 Quick Start Guide

### 1. Bootstrapping the OS
Brain uses a fast, automated setup script to install dependencies (like `uv`) and configure your environment.

**Mac / Linux Users:**
```bash
./setup.sh
```

**Windows Users:**
```powershell
./setup.ps1
```

### 2. API Keys
The setup script created a `.env` file in your directory. Open it and add your API keys.
*Note: Brain defaults to Anthropic's Claude 3.5. If you only have an `OPENAI_API_KEY`, don't worry—the OS will automatically detect this and safely route your tasks to GPT-4o.*

### 3. Vault Initialization
Because Brain is privacy-first, your personal data directories are ignored in git. Build your safe vault structure and foundational memory files instantly:
```bash
uv run python System/cli.py init
```

---

## 🔮 The Obsidian UI (The Glass Pane)

Brain uses the local file system as its database, but **Obsidian** is its official UI. Because we check the `.obsidian/` folder into version control, your vault comes pre-configured with a highly opinionated "Second Brain" layout.

### 1. The Control Room (`Home.md`)
When you open the vault, you will land on `Home.md`. This is your OS Dashboard. It provides instantaneous links to your active Forge projects (`Studio/`), your scratchpad, and your system logs.

### 2. The Media Quarantine
By default, pasting images into markdown clutters the root directory. Brain prevents this.
When you paste an image or PDF into any file in Obsidian, it is automatically routed to `Media/Attachments/`.
* **The Forge Workflow:** If you want an AI to use an image in a web app, do not put the image in the web app folder. Drop it into Obsidian, then command the OS: `"Copy Media/Attachments/image.png to Studio/My-App/public/logo.png"`.

### 3. The Clean Knowledge Graph
Obsidian's Graph View is powerful, but indexing `node_modules` and Python caches ruins it.
* Brain uses hidden `userIgnoreFilters` to completely banish build files and dependencies from Obsidian's index.
* To filter out raw code files from your graph, open the Graph Settings and set the search filter to: `-path:Studio`

### 4. Running Commands Natively (Zero Alt-Tab)
You do not need to open a separate terminal to command Brain. The vault is pre-configured with the **Shell Commands** plugin.
1. Map **Queue Task**: `.\.venv\Scripts\python.exe System\cli.py task "{{_task}}" --obsidian` *(Bind to `Cmd/Ctrl + Shift + B`)*
2. Map **Execute Queue**: `.\.venv\Scripts\python.exe System\cli.py execute-pending` *(Bind to `Cmd/Ctrl + Shift + Enter`)*

---

## 💻 Usage & Commands

Brain operates via a unified CLI router (`System/cli.py`).

### Execute a Task (Terminal Mode)
If you aren't using the Obsidian GUI, you can run tasks directly. The system will auto-route, assign domains, and spin up the necessary agents safely.
```bash
uv run python System/cli.py task "Help me brainstorm a marketing plan for my project."
```

### View Telemetry & Logs
Brain logs every token, prompt, and action for perfect local observability.
```bash
uv run python System/cli.py logs --limit 3
```

### 🌙 The Biological Sleep Cycle (Memory Consolidation)
Inspired by human biology and Anthropic's "Dreams" architecture, Brain OS features a multi-phase memory consolidation system to ensure zero context bloat and data safety.

1. **The Hippocampus (Capture):** Throughout the day, the OS logs fast, unstructured agent interactions to `logs/agent_interactions.jsonl`.
2. **NREM Sleep (Filtration):** When you execute `sleep`, the OS parses the JSONL, truncating massive code payloads to extract pure conceptual intents.
3. **Immutable Versioning:** The OS creates a read-only timestamped backup of your current `.md` files in `logs/backups/`.
4. **REM Sleep (Synaptic Pruning):** The Auditor LLM analyzes the daily log against your existing Markdown memories. It identifies persistent facts, marks old logic as `Superseded` (rather than blindly overwriting history), and maintains a strict 100KB file-size rule.
5. **Amnesia (Log Rotation):** The daily JSONL is archived, wiping the short-term memory clean for the next day.

```bash
uv run python System/cli.py sleep
```

---

## ⚙️ Customizing Agents & Pipelines

You never need to touch Python code to change how Brain thinks. Everything is controlled via `System/config/agents.yaml`.

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

---

## 🏭 Forge: The Factory Floor

Brain acts as the Project Manager, but it delegates application builds to **Forge**—a deterministic, ATDD-driven React/Python template that lives in your `Studio/` directory.

### 1. Installing Forge
Brain manages the complete scaffolding and dependency hydration (Shift-Left) for new Forge projects. To spin up a new application:
```bash
uv run python System/cli.py task "Use bootstrap_project to create a new project called 'My-App' using the Forge template."
```
*Note: `bootstrap_project` automatically clones the repository, renames the remote to `upstream`, and runs `npm install` and `uv sync`.*

### 2. Updating Forge from Remote
Because Brain renames the original Forge repository remote to `upstream` during installation, you can easily pull the latest architectural updates from the master Forge template without overwriting your custom app code:
```bash
uv run python System/cli.py task "Run execute_command to 'git fetch upstream' and 'git merge upstream/main' inside Studio/My-App"
```

### 3. Prompting Forge (Ticket-Driven Delegation)
**Never play the "Telephone Game"** by passing dense, multi-step requirements directly into the `operate_forge` command prompt. Instead, use the real-world PM workflow: write a ticket, and tell the engineer to read the ticket.

**The Best-Practice Workflow:**
1. **Stage Assets:** Use Brain to move any images from `Media/` to the Forge `public/` directory.
2. **Write the Ticket:** Instruct Brain to write the requirements into `Studio/My-App/docs/product/current_run.md`.
3. **Dispatch the Worker:** Run `operate_forge` with a minimal instruction.

*For overly complex refactors, use the "Payload Drop" method: Have Brain write the complete raw code to `docs/product/payload.txt`, and instruct Forge to simply copy-paste it into the target file.*

### 4. Debugging Forge (The Ghost in the Machine)
If Forge reports `Exit Code 0 (Success)` but your browser does not reflect the changes, **do not assume the system is broken.** You are likely experiencing AI Attention Collapse or a "Ghost File" (where the AI successfully wrote the code, but to a hallucinated/orphaned file path).

**The Debug Protocol:**
1. **Check Telemetry:** Open `Studio/My-App/docs/ops/telemetry.jsonl`. This file contains the exact, unedited JSON payload the AI executed.
2. **Verify Paths:** Check if the AI wrote to `src/web/Hero.tsx` instead of `src/web/components/Hero.tsx`.
3. **Check the Router:** Ensure the AI didn't accidentally update `main.tsx` to point to a dead file.
4. **Fix via Brain:** Instruct the `WORKSPACE` route in Brain to delete the orphaned files and fix the imports.

---

## 🤝 Contributing
Contributions to the core routing engine and API layers are welcome. Because Brain values Shift-Left engineering, **we enforce strict 100% test coverage on all security and execution bypass logic.**

Please ensure all tests and linters pass before submitting a PR:
```bash
uv run pytest System/tests/ --cov
uv run ruff check .
```

---
*Brain — Designed for humans to collaborate safely with AI.*
