# 🧠 Brain OS: Biomimetic Agentic Control Plane

![Architecture](https://img.shields.io/badge/Architecture-Biomimetic--Multiagent-purple.svg) ![Security](https://img.shields.io/badge/Sandbox-Deno_WASM-red.svg) ![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg) ![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

> **Note to Systems Engineers:** I took the biomimicry domain-driven design quite far (e.g., the routing matrix is the `Medulla`, memory is the `Hippocampus`). It might look eccentric, but underneath is a highly optimized, concurrent, lock-safe, and zero-debt execution engine.

**Brain OS** is a fully local, headless AI operating system inspired by human neuroanatomy and the Unix Philosophy. It operates directly on your local file system, orchestrates multi-agent swarms, and executes code within strict WebAssembly sandboxes.

*(📸 PLACE YOUR SPLIT-SCREEN TERMINAL GIF HERE SHOWING A 0-TOKEN TASK EXECUTION)*

---

## ⚡ The "Aha!" Moment (Quickstart)

Brain OS operates on pure text and local embeddings, meaning you can parse your entire codebase before spending a single API token.

**1. Absorb a workspace (0 Token Cost - Local Embeddings)**
```bash
./brain absorb ./my_project
```
**2. Execute a sandboxed agentic task**
```bash
./brain task "Audit ./my_project for concurrency race conditions and output to audit.md"
```
**3. Native Unix Piping**
```bash
cat error.log | grep "Timeout" | ./brain task "Explain this failure cascade"
```

---

## 🚀 Installation (Zero-Debt & Frictionless)

We hate global dependencies. Brain OS provides two strictly isolated installation paths:

### Option A: The Docker Sandbox (Recommended)
Zero host dependencies. Runs Brain OS inside an isolated container with local workspace volume mounting.
1. `git clone https://github.com/mrdanielcasper/brain.git && cd brain`
2. `docker compose build`
3. Run `./brain` (or `.\brain.bat` on Windows). The wrapper automatically resolves path relative offsets, enforces absolute host mounts, and routes calls through the isolated sandbox securely.

### Option B: Lightning Local (`uv`)
Uses Astral's ultra-fast `uv` to resolve dependencies in seconds inside an isolated `.venv`.
1. `git clone https://github.com/mrdanielcasper/brain.git && cd brain`
2. Run `./setup.sh` (Mac/Linux) or `.\setup.ps1` (Windows).
3. The script auto-hydrates the `.venv`, configures the local Deno sandbox environment, and launches the interactive `Synaptic Genesis` wizard.

*Have Ollama running? The setup script will auto-detect it on `localhost:11434` for 100% air-gapped, offline execution.*

---

## 🔐 Security & Sandboxing (Clear-Box Transparency)

Running LLM-generated code locally is inherently dangerous. Brain OS implements a strict containment matrix:

1. **The Deno WASM Jail:** If "Agentic Mode" is enabled, Brain does *not* run generated code in your native Python or Bash environment. It forces the LLM to write TypeScript/JavaScript, which is then executed inside an ephemeral, unprivileged **Deno WebAssembly** instance.
2. **The Volume Mask:** The agent is physically incapable of seeing files outside the directory you explicitly bound during setup.
3. **Cognitive Fallback:** If Deno is not installed (or not running in Docker), the system safely degrades to **Cognitive Mode**, where the LLM can only read and write files, stripping its ability to execute subprocesses entirely.

---

## 📁 Workspace Agnosticism (Optional Obsidian Integration)

**Brain OS expects text and outputs text.** You can point it at any standard directory, VSCode project, or Logseq graph.

However, if you point it at an **Obsidian Vault**, Brain OS will automatically detect the `.obsidian` configuration folder and atomically configure native hotkeys (`Ctrl+Alt+S`).
*Note: To map active shell commands directly to these hotkey bindings from within the graphic editor interface, please ensure the standard `obsidian-shellcommands` community plugin is active in your vault.*

---

## ⌨️ Core Commands

* `brain setup`: Boot the interactive onboarding wizard to configure API keys, LLM routing, and workspace bindings.
* `brain task "<prompt>"`: Dispatches a multi-agent swarm to accomplish a goal.
* `brain daydream`: Triggers the Default Mode Network (DMN) to autonomously organize files, compress old memories, and refactor code in the background.
* `brain status`: Opens the real-time Cortical Telemetry dashboard to monitor active agent loops and memory usage.

### 💀 Systemic Apoptosis (Zero-Residue Uninstall)
If you are done with Brain OS, leave no trace behind:
```bash
./brain destroy
```
*This securely purges all local ledgers, token tracking logs, environment API keys, and execution queues. It respects your machine.*

---

## 🤝 Contributing
Brain values Shift-Left engineering. We enforce strict 100% test coverage on all security, file locking, and execution bypass logic. To verify your PR against our automated gates:
```bash
uv run pytest System/tests Sense/tests -v
uv run ruff check .
```
