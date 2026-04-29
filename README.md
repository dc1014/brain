# 🧠 Brain OS: The Multi-Agent Life Operating System

![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-purple.svg)
![License](https://img.shields.io/badge/License-MIT%20(Open%20Core)-green.svg)

Brain OS is a local-first, privacy-centric "Second Brain" and autonomous agent ecosystem. It bridges the gap between your local file system, unstructured thoughts, and LLM reasoning engines. 

Instead of an expensive, wandering AI that hallucinates in a black box, Brain OS uses **Shift-Left Engineering**. It utilizes a deterministic router to mathematically bound the AI, pre-calculate execution tracks, and strictly sandbox file operations. It is designed to be **"The Vim of AI"**—fast, token-optimized, observable, and highly secure.

---

## 🌟 Core Philosophy (The Open-Core Model)
1. **Privacy Absolute:** Your data (Vault), journals, and business IP never leave your machine to be stored on third-party servers. All folders are aggressively `.gitignore`d.
2. **Zero-Waste Token Economics:** Context limits are respected. The system dynamically extracts payloads and drops intermediate reasoning steps to keep loops lean.
3. **Open-Core Engine:** The routing system, API logic, and prompts are 100% open-source. Advanced hardware-accelerated features (like GPU Synaptic Memory) are handled via private, drop-in plugins.

---

## 🏗️ Architecture

### 1. The Deterministic Router (Shift-Left Bouncer)
Before an expensive agent ever boots up, a high-speed Auditor model (GPT-4o-mini) intercepts the prompt. It enforces hard security rules (e.g., blocking `rm` commands or access to system files) and calculates the **Intent Domain** and **Execution Route** (`FAST`, `READ_ONLY`, or `COMPLEX`).

### 2. The Multi-Agent Trinity
Powered by `uv` and `LiteLLM`, the OS orchestrates three specialized models:
* **The Auditor (`gpt-4o-mini`):** The Bouncer. Evaluates prompts, assigns domain context (Personal, Professional, Studio), and runs the nightly memory compaction.
* **The Worker (`claude-3-5-haiku`):** The Engineer. Given sandboxed tools, it explores directories, reads files, and writes code/markdown safely.
* **The Orchestrator (`gemini-2.5-flash`):** The Synthesizer. Reviews the Worker's draft and actions, compiling them into polished executive summaries. Answers `FAST` route queries instantly.

### 3. Hierarchical Context Engineering
The OS dynamically stacks memory. It always injects `Meta/global-memory.md` (your core identity), but uses intent-mapping to selectively inject `Personal/personal-memory.md` or `Studio/studio-memory.md` based on the active task, saving massive amounts of tokens.

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python 3.14+**
* **[uv](https://github.com/astral-sh/uv):** The blazingly fast Python package manager.

### 1. Clone & Install
Clone the core engine and lock in the dependencies:
```bash
git clone [https://github.com/yourusername/brain.git](https://github.com/yourusername/brain.git)
cd brain
uv sync
```

### 2. Vault Initialization (Critical Step)
Because Brain OS is strictly privacy-first, your personal data directories are ignored in git. **You must create the folder structure manually:**

```bash
# Create the secure Vault boundaries
mkdir Personal Professional Studio Meta Plugins logs

# Create the foundational memory files
touch Meta/global-memory.md
touch Personal/personal-memory.md
touch Professional/professional-memory.md
touch Studio/studio-memory.md
```
*(Pro-tip: Open `Meta/global-memory.md` and write a brief description of who you are and what your goals are. The AI will use this in every interaction.)*

### 3. Configure Environment
Copy the example environment file and add your API keys:
```bash
cp .env.example .env
```
Populate `.env` with your `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, and `OPENAI_API_KEY`.

---

## 💻 Usage & Commands

Brain OS operates via a unified CLI router. 

### Execute a Task
The system will auto-route, assign domains, and spin up the necessary agents.
```bash
uv run System/router.py task "Help me brainstorm a marketing plan for my Open-Core project."
```

### View Telemetry & Logs
Brain OS logs every token, prompt, and action for perfect local observability.
```bash
uv run System/router.py logs --limit 3
```

### 🌙 The Sleep Cycle Compactor (Memory Synthesis)
At the end of the day, command the OS to sleep. The Auditor will read your daily `logs/agent_interactions.jsonl`, extract permanent high-value facts (strategies, preferences, coding rules), inject them directly into your Markdown memory files, and safely rotate/archive the logs.
```bash
uv run System/router.py sleep
```

---

## 🔌 Phase 4: Synaptic Memory (Pro Plugin)
Brain OS ships with **Tier 1 Symbolic Memory** (Markdown). 

If you have purchased the **Brain OS Synaptic Pro** plugin, you can enable hardware-accelerated **Tier 2 Memory** using local GPU LoRA weight training (`.safetensors`).
To trigger this, simply drop `synaptic_engine.py` into your `Plugins/` folder and run:
```bash
uv run System/router.py sleep --synaptic
```
*If the plugin is not detected, the OS gracefully falls back to Tier 1 Markdown memory.*

---

## 🛡️ Security & Sandboxing
The Worker agent is completely sandboxed. It can only execute explicit Python tools (`write_safe_file`, `read_safe_file`, `list_safe_directory`) scoped strictly to the `Personal/`, `Professional/`, and `Studio/` directories. Attempts to traverse directories (`../`), access `.env`, or write to the system kernel are mathematically blocked at the tool layer.

## 🤝 Contributing
Contributions to the core routing engine and API layers are welcome. 
Please ensure all tests pass before submitting a PR:
```bash
uv run pytest System/tests/
uv run ruff check .
```

---
*Brain OS — Designed for humans. Executed by agents.*