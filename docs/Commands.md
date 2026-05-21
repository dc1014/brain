# 🕹️ Ecosystem Command Interface: Complete Somatic & Sensory Command Manifest

This manifest documents the complete, un-truncated suite of command-line interfaces exposed across the Brain OS ecosystem. It captures every command registered within the core execution bootloader (`System/cli.py`) and the decoupled sensory receptor interface (`Sense/cli.py`), mapped directly to their corresponding software file paths and biological neuroanatomy analogs.

---

## 🎯 Quick Reference: Ecosystem Command Matrix

| CLI Invocation Track | Core Target Module | Architectural Safety Guardrail |
| --- | --- | --- |
| `System/cli.py live` | `systemic/thymus.py` | Creates an out-of-process watchdog using secure named pipes to monitor child processing loops. |
| `System/cli.py task` | `core/orchestrator.py` | Decomposes task requests through Thalamic filters to safeguard multi-agent swarms. |
| `System/cli.py watch` | `cli_somatic.py` | Runs continuous background folder event monitoring, executing zero-cost lints on file save. |
| `System/cli.py reindex` | `limbic/hippocampus.py` | Rebuilds full-text search tables to index plaintext code vectors safely. |
| `Sense/cli.py scrape` | `receptors/web.py` | Performs upfront DNS host verification to block loops to private subnets (SSRF safety). |
| `Sense/cli.py smell` | `sensory/olfactory.py` | Runs localized folder rules and regex checks at zero token cost to map tech debt or broken file link paths. |
| `Sense/cli.py taste` | `receptors/taste.py` | Cross-sections high-density CSV, PDF, and log files to protect context windows. |

---



## 🧠 Part 1: Core System & Administration Interfaces (`System/cli.py`)

All commands in this section are executed via Typer using the core cognitive bootloader entry point:

```bash
uv run System/cli.py [COMMAND]

```

### 🔋 1. `live` (The Thymus Watchdog Ignition)

* **Subsystem Core Path:** `System/neuroanatomy/systemic/thymus.py`
* **Biological Analog:** Thymus Gland / Parent Process Supervisor
* **Mechanics:** Instantiates the out-of-process system watchdog. This launches the master orchestration brainstem (`MedullaOblongata`) inside an isolated child subprocess, setting up named pipe or UNIX socket communication streams to track execution speeds and respond to rogue thread spikes.

### 🛑 2. `halt` (The Nervous System Severance)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/vagus_nerve.py`
* **Biological Analog:** Vagus Nerve Circuit Breaker
* **Mechanics:** Issues an immediate runtime block signal to the active process structures. This safely cuts off active multi-agent queues, detaches active background daemons, and winds down processing cycles cleanly to prevent memory or transaction corruption.

### 🔄 3. `recover` (The Homeostatic State Realignment)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/vagus_nerve.py`
* **Biological Analog:** Vagus Nerve Reflex Reset
* **Mechanics:** Clears locked error loops and high-stress system triggers, restoring the central orchestration environment back into an active, ready state.

### 🔓 4. `approve` (The Dopaminergic Inhibition Release)

* **Subsystem Core Path:** Local Obsidian UI Registry
* **Biological Analog:** Nucleus Accumbens / Reward Gate Release
* **Mechanics:** Drops an atomic approval token flag (`.approved`) in `Meta/` to authorize items pending inside the markdown queue. It automatically updates the user-facing workspace file `Meta/Pending_Actions.md` and signals the background Medulla daemon worker loop to execute the approved tasks.

### 🧬 5. `setup` (The Interactive Onboarding Genesis)

* **Subsystem Core Path:** `System/core/onboarding.py`
* **Biological Analog:** Synaptic Genesis Initialization
* **Mechanics:** Triggers an interactive setup wizard that configures required system parameters, paths, and platform secrets, cleanly encapsulating credentials into the immune storage vault.

---

## 🧠 Part 2: Central Nervous System (CNS) Cognitive Tracking

These commands route complex processing workflows and background drive states through the core reasoning layers.

### 🎯 1. `task`

* **Biological Analog:** Prefrontal Cortex / Goal Decomposition & Executive Function
* **Mechanics:** Dispatches high-level instructions into the core orchestrator engine. Tasks are intercepted by the Thalamus for intent validation before being broken down into structured step pipelines for multi-agent swarm execution.

### 🌌 2. `daydream`

* **Biological Analog:** Default Mode Network / Asynchronous Optimization
* **Mechanics:** Forces the background reflection system to scan recent error footprints and random markdown notes. This synthesizes non-obvious optimizations or design hypotheses, which are logged directly to `daydreams.md`.

### 🎛️ 3. `evolve`

* **Biological Analog:** Neuroplasticity / Structural Synaptic Rewiring
* **Mechanics:** Evaluates systemic execution logs and failure indicators to programmatically alter internal configuration structures, modifying model attributes or rewriting agent system prompts over time.

### 🦅 4. `forage`

* **Biological Analog:** Ultradian Drives / Environmental Information Gathering
* **Mechanics:** Periodically checks scheduled web endpoints, technical tracking boards, or log metrics, summarizing the retrieved indicators into morning context briefings.

### 🗃️ 5. `compile`

* **Biological Analog:** Cerebellum / Procedural Engram Ingestion
* **Mechanics:** Converts multi-step command blocks or verified engineering sequences into standalone, parameter-driven shell script modules for automated reuse.

### 🧫 6. `absorb`

* **Biological Analog:** Parietal Lobe / Structural Context Ingestion
* **Mechanics:** Parses workspace folder structures, tracking explicit dependency changes to update internal context definitions.

---

## 🦾 Part 3: Somatic (Reflex & Status Layer) Controls

These interfaces drive local repository infrastructure, tracking metrics, and immediate automated reflexes.

### 🗺️ 1. `map-topology`

* **Biological Analog:** Parietal Lobe / Code Blueprint Topology
* **Mechanics:** Recursively parses the Abstract Syntax Tree (AST) of active internal modules via `ast.walk()`, generating syntax-validated Mermaid layout graphs of how subsystems talk to each other while filtering out third-party clutter.

### 📊 2. `status`

* **Biological Analog:** Interoception / Core Vitals Check
* **Mechanics:** Displays live performance metrics, tracking active background process groups, recent memory indexing states, and remaining token limits.

### 📜 3. `list-reflexes`

* **Biological Analog:** Somatosensory / Reflex Blueprint Audit
* **Mechanics:** Identifies all zero-token event-driven handlers registered inside the local execution memory.

### ⚡ 4. `reflex`

* **Biological Analog:** Somatosensory / Instant Involuntary Action
* **Mechanics:** Manually triggers a zero-token local execution script—such as checking workspace code formatting via `ruff` or parsing text link states—bypassing high-overhead model calls.

### 💤 5. `sleep`

* **Biological Analog:** Pineal Gland / Circadian Rest Phase
* **Mechanics:** Triggers an immediate deep sleep sequence. This flushes temporary files, compiles active workspace interaction streams into permanent Markdown logs, and activates background optimization loops.

---

## 👁️ Part 4: Sensory Receptor Operations (`Sense/cli.py`)

All commands in this section execute via the standalone `Sense` utility:

```bash
uv run Sense/cli.py [COMMAND]

```

### 🕸️ 1. `scrape [URL]`

* **Biological Analog:** The Retina / Web Sensory Transduction
* **Mechanics:** Passes input links through an upfront Server-Side Request Forgery (SSRF) firewall, checking DNS names against a private IP blacklist before opening requests. Once validated, it uses headless Chromium via Playwright to fetch the layout page, strips out presentation artifacts (`script`, `nav`, `style`), and outputs clean text to standard out.

### 🌊 2. `flush`

* **Biological Analog:** The Lymphatic System / Metabolic Waste Collection
* **Mechanics:** Sweeps temporary file definitions, workspace log data, and duplicate `.bak` file snapshots generated by file modifications, packing them into compressed tarball archives inside `Meta/Lymph_Nodes/`.

### 💀 3. `purge`

* **Biological Analog:** The Lymphatic System / Destructive Waste Removal
* **Mechanics:** Performs a hard, non-recoverable file-system deletion of all compressed Lymph Node backup archives to reclaim storage space on the host machine.

### 🌙 4. `sleep`

* **Biological Analog:** Pineal Gland / Synaptic Consolidation Bridge
* **Mechanics:** An interface bridge that manually triggers a complete subcortical rest sequence, executing both Lymphatic waste flushing and REM memory consolidation.

### 📸 5. `screenshot [URL] [OUTPUT_FILE]`

* **Biological Analog:** The Visual Cortex / Environment Image Capture
* **Mechanics:** Launches a headless browser session via Playwright to take a high-fidelity full-page image snapshot of any target application or server URL.

### 👁️ 6. `perceive [IMAGE_PATH] [QUERY]`

* **Biological Analog:** Occipital Lobe / Multimodal Asset Evaluation
* **Mechanics:** Routes local image files or full-page screenshots straight to vision models, translating design structures or styling variations into clear textual context.

### 🎤 7. `listen [--duration -d] [--output -o]`

* **Biological Analog:** The Physical Ear / Waveform Audio Ingestion
* **Mechanics:** Locks onto the host machine's physical hardware microphone drivers to record real-time audio at a clean 44.1kHz sample rate. If no absolute path destination is supplied, it isolates the recording into the `Media/Recordings/` directory to satisfy media quarantine standards.

### 🔊 8. `speak [FILE_PATH]`

* **Biological Analog:** The Physical Mouth / Subcortical Signal Output
* **Mechanics:** Bypasses LLM planning layers to play back raw audio tracks or speech files directly through the host hardware speaker drivers.

### 👃 9. `smell [DIRECTORY_NAME]`

* **Biological Analog:** The Olfactory Bulb / Zero-Token Static Decay Auditing
* **Mechanics:** Runs fast repository cleanup sweeps at zero token cost. It parses local folders using file rules and regex math to detect broken links, empty notes, or formatting decay, writing issues directly to `Meta/Olfactory_Anomalies.md` for agents to resolve during consolidation.

### 👅 10. `taste [FILE_PATH]`

* **Biological Analog:** The Gustatory System / Context-Preserving Ingestion
* **Mechanics:** Processes dense or massive local resource structures (PDF tables, heavy logs, CSV files) by chunking and cross-sectioning content. This extracts file structure indicators while stripping out repetitive blocks, ensuring context windows remain slim.

---
