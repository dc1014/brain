# 🧠 CoreTex: Biomimetic Agentic Control Plane and Knowledge Engine

![Architecture](https://img.shields.io/badge/Architecture-Biomimetic--Multiagent-purple.svg) ![Security](https://img.shields.io/badge/Sandbox-Deno_WASM-red.svg) ![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg) ![Coverage](https://img.shields.io/badge/Coverage-80%25-green.svg) ![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

> **Note to Systems Engineers:** I took the biomimicry domain-driven design quite far (e.g., the master daemon is the `Medulla`, short-term memory is the `Hippocampus`). It might look eccentric, but underneath is (arguably) a highly optimized, concurrent, lock-safe, and zero-debt execution engine.

**CoreTex** is a fully local, headless AI operating system inspired by human neuroanatomy and the Unix Philosophy. It operates directly on your local file system, orchestrates multi-agent swarms, and executes code within strict WebAssembly sandboxes.

*(📸 PLACE YOUR SPLIT-SCREEN TERMINAL GIF HERE SHOWING A 0-TOKEN TASK EXECUTION)*

---

### 🏗️ Architectural Highlights
1. **0-Token Ingestion:** Absorb and index your local workspace using local embeddings (`uv` + local python scripts) with **0 external API calls**. You can read, index, and organize your private vault without spending money or leaking data.
2. **Safe-by-Default Execution:** The default "Cognitive Mode" is strictly read/write advisory. Active shell or script execution requires explicit user consent, and is hard-isolated inside an offline Deno-hosted V8 WebAssembly jail with strict CPU/memory caps and filesystem masking. Or just run it in Docker.

---

## ⚡ The "Aha!" Moment (Quickstart)

CoreTex operates on pure text and local embeddings, meaning you can parse your entire codebase before spending a single API token.

**1. Absorb a workspace (0 Token Cost - Local Embeddings)**
```bash
ctx absorb ./my_project
```
**2. Execute a sandboxed agentic task**
```bash
ctx task "Audit ./my_project for concurrency race conditions and output to audit.md"
```
**3. Native Unix Piping**
```bash
cat error.log | grep "Timeout" | ctx task "Explain this failure cascade"
```

---

## 🚀 Installation (Zero-Debt & Frictionless)

CoreTex features a unified, self-healing installation pipeline that automates all prerequisite matching, virtual environments, and secure container structures out of the box. Clone the repository and run the setup utility matching your host environment:

### 🍏 macOS & 🐧 Linux
```bash
chmod +x setup.sh && ./setup.sh
```
*Note: The script automatically evaluates your localized package manager (`apt`, `dnf`, `pacman`, `apk`, or `brew`) to resolve missing system dependencies like `unzip` headlessly.*

### 🔷 Windows (PowerShell)
To bypass native Windows script execution restrictions safely without modifying your global system security profile, execute the script via this process-isolated command:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

### 🛡️ Enterprise API Gateways & Proxies
CoreTex OS natively supports routing your LLM traffic through enterprise API Gateways (like **Cloudflare AI Gateway**, **Portkey**, or **Helicone**) to centralize observability, rate-limiting, and cost tracking.

During the interactive `ctx setup` phase, simply select `[Gateway]` to provide your proxy URL and Gateway API Token. CoreTex will seamlessly inject the `api_base` into the execution stream, keeping your traffic monitored and secure.

---

## 🪐 The Deployment Pathways

The setup utility will probe your environment and offer two distinct runtime architectures:

### 1. Pure Local Deployment (Recommended)
Installs Astral's hyper-fast `uv` package manager and the `deno` secure runtime natively on your host machine. CoreTex executes directly on your file system, using local loops while isolating third-party code blocks inside a secure cryptographic WebAssembly jail.

### 2. Isolated Container Deployment (Zero-Dependency)
Requires Docker. The script handles all host user UID/GID mapping permissions natively to avoid root-owned directory pollution, seeds local environment states, and transparently pipes your session directly into the interactive setup plane.

---

## 🧬 Synaptic Genesis (Interactive Setup)

Regardless of the installation route selected above, you will be launched into the high-fidelity **Synaptic Genesis** wizard to complete initialization:

1. **Operating Profile Boundary:** Lock your environment to *Cognitive Mode* (advisory, safe file interactions) or *Agentic Mode* (sandboxed system execution via the Deno WASM engine).
2. **Sensory Innervation:** Toggle layout-auditing vision scrapers (Playwright/Chromium) or hardware microphone/speaker channels natively.
3. **Synaptic Handshake:** Securely link cloud providers (OpenAI, Anthropic, Gemini) or local private backends (Ollama).
4. **Workspace Binding:** Wire CoreTex to any local directory or an Obsidian vault (which automatically injects custom hotkey configurations).

Once complete, restart your terminal app to load environment changes, and control the entire operating plane using the global shorthand command:
```bash
ctx --help
```

---

## 🔐 Security & Sandboxing (Clear-Box Transparency)

Running LLM-generated code locally is inherently dangerous. CoreTex implements a strict containment matrix:

1. **The Deno WASM Jail:** If "Agentic Mode" is enabled, CoreTex does *not* run generated code in your native Python or Bash environment. It forces the LLM to write TypeScript/JavaScript, which is then executed inside an ephemeral, unprivileged **Deno WebAssembly** instance.
2. **The Volume Mask:** The agent is physically incapable of seeing files outside the directory you explicitly bound during setup.
3. **Cognitive Fallback:** If Deno is not installed (or not running in Docker), the system safely degrades to **Cognitive Mode**, where the LLM can only read and write files, stripping its ability to execute subprocesses entirely.

---

## 📁 Workspace Agnosticism (Optional Obsidian Integration)

**CoreTex expects text and outputs text.** You can point it at any standard directory, VSCode project, or Logseq graph.

However, if you point it at an **Obsidian Vault**, CoreTex will automatically detect the `.obsidian` configuration folder and atomically configure native hotkeys (`Ctrl+Alt+S`).
*Note: To map active shell commands directly to these hotkey bindings from within the graphic editor interface, please ensure the standard `obsidian-shellcommands` community plugin is active in your vault.*

---

## ⌨️ Core Commands

* `ctx setup`: Boot the interactive onboarding wizard to configure API keys, LLM routing, and workspace bindings.
* `ctx task "<prompt>"`: Dispatches a multi-agent swarm to accomplish a goal.
* `ctx daydream`: Triggers the Default Mode Network (DMN) to autonomously organize files, compress old memories, and refactor code in the background.
* `ctx status`: Opens the real-time Cortical Telemetry dashboard to monitor active agent loops and memory usage.

### Sensory Perception Subcommands (Sense Module)
Trigger CoreTex OS's external receptors directly from the execution plane:
* `ctx sense screenshot "https://google.com" "google.png"` - *Takes a headless web screenshot.*
* `ctx sense perceive "google.png" "Describe layout"` - *Uses the Occipital Lobe to analyze visual stimuli.*
* `ctx sense scrape "https://github.com"` - *Transduces a web page into raw markdown text format.*
* `ctx sense listen --duration 10` - *Activates physical microphone hardware receptors.*
* `ctx sense speak output.wav` - *Dispatches sound arrays down physical speaker hardware channels.*

### 💀 Systemic Apoptosis (Zero-Residue Uninstall)
If you are done with CoreTex, leave no trace behind:
```bash
ctx destroy
```
*This securely purges all local ledgers, token tracking logs, environment API keys, and execution queues. It respects your machine.*

---

## 🤝 Contributing
CoreTex values Shift-Left engineering. We enforce strict 100% test coverage on all security, file locking, and execution bypass logic. To verify your PR against our automated gates:
```bash
uv run pytest System/tests Sense/tests -v
uv run ruff check .
```
