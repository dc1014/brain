# 🧠 Brain: The Life OS

![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-purple.svg)
![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)

Brain is an open-source "Second Brain" and semi-autonomous agent ecosystem. It bridges the gap between your local file system, unstructured thoughts, LLM reasoning engines, and MCP servers while being as safe as I can make it and minimizing token usage.

 Brain uses **Shift-Left Engineering** and **The Unix Philosophy** as a generalized principle. Everything is a file so you can see and change everything. It utilizes a deterministic router to bound the AI, pre-calculate execution tracks, and strictly sandboxed file operations. It is designed to be fast, token-optimized, observable, highly secure, and copletely open.

---

## 🌟 Core Philosophy
1. **Own Your Brain:** Your Brain and everything in it - data (Vault), journals, art, code, and business IP - is yours. All personal folders are aggressively `.gitignore`d.
2. **Zero-Waste Token Economics:** Context limits are respected. The system dynamically extracts payloads and drops intermediate reasoning steps to keep context loops lean.
3. **Open-Source & UNIX-Native:** Everything is a file. The routing system, API logic, memory structures, and prompts are 100% open-source and run entirely on your machine.
---

## 🏗️ Architecture

### 1. The Deterministic Router (Shift-Left Bouncer)
Before an expensive agent ever boots up, a high-speed Auditor model intercepts the prompt. It enforces hard security rules (e.g., blocking `rm` commands or access to system files) and calculates the **Intent Domain** and **Execution Route** (`FAST`, `READ_ONLY`, or `COMPLEX`).

### 2. The Multi-Agent Trinity
Powered by `uv` and `LiteLLM`, the OS orchestrates three specialized models:
* **The Auditor:** The Bouncer. Evaluates prompts, assigns domain context (Personal, Professional, Studio), and runs the nightly memory compaction.
* **The Worker:** The Engineer. Given sandboxed tools, it explores directories, reads files, and writes code/markdown safely.
* **The Orchestrator:** The Synthesizer. Reviews the Worker's draft and actions, compiling them into polished executive summaries.

*(Note: Brain features a **Zero-Config Fallback**. Supply keys for Anthropic, Google, and OpenAI to use the full Trinity, or supply just ONE key and the system will gracefully map all roles to that single model).*

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

### 🌙 The Sleep Cycle Compactor (Memory Synthesis)
At the end of the day, command the OS to sleep. The Auditor will read your daily `logs/agent_interactions.jsonl`, extract permanent high-value facts (strategies, preferences, coding rules), inject them directly into your Markdown memory files, and safely rotate/archive the logs.
```bash
uv run System/router.py sleep
```

---

## 🛡️ Security & Sandboxing
The Worker agent is completely sandboxed. It can only execute explicit Python tools (`write_safe_file`, `read_safe_file`, `list_safe_directory`, `append_safe_file`) scoped strictly to your vault directories. Attempts to traverse directories (`../`), access `.env`, or write to the system kernel are mathematically blocked at the tool layer.

## 🤝 Contributing
Contributions to the core routing engine and API layers are welcome. 
Please ensure all tests pass before submitting a PR:
```bash
uv run pytest System/tests/
uv run ruff check .
```

---
*Brain — Designed for humans. Executed by agents.*