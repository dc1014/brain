# 🧬 CoreTex OS Biomimetic Architecture: Complete Neuroanatomical Blueprint

CoreTex OS rejects the paradigm of simple linear state machines and unmanaged agent scripts. Instead, it implements a **completely unified, self-maintaining cognitive engine** modeled directly on human neuroanatomy and evolutionary biology. Every directory, daemon, and file tracking boundary functions as a biological analog designed to maximize context efficiency, defend resource balances, and automate code generation without technical debt.

---

## 🎯 Summary of System Directories & Core Architectural Domains

| System Domain Folder | Neuroanatomical Layer | Core Engineering Control Mechanism |
| --- | --- | --- |
| **`Sense/receptors/`** | Peripheral Sensory Network | Encapsulates raw HTTP, TCP socket data, and hardware audio streams into clean context lines before data ascends to reasoning layers. |
| **`System/autonomic/`** | Brainstem Life-Support Engine | Manages persistent daemon loops, interoceptive token monitoring caps, transaction logs, and hardware server management. |
| **`System/limbic/`** | Subcortical Filter & Validation Matrix | Controls fast SQLite search tables, pre-flight threat mitigation engines, and ACC load hooks that block link database pollution. |
| **`System/cortical/`** | Executive Function & Optimization Center | Decomposes task backlogs into actionable sequences, runs type-safe code generation blocks, and compresses working buffers. |
| **`System/systemic/`** | Endogenous Immune & Firewall Protection | Operates Ahead-of-Time AST module parsers, python audit hooks, key environment scrubbing, and out-of-process watchdog jailing. |

---

## 🧠 Group 1: Memory Subsystems & Subcortical Indexing

### Ephemeral Indexing Tables (The Hippocampus)

* **Subsystem Core Path:** `System/neuroanatomy/limbic/hippocampus.py`
* **Mechanics:** Functions as the primary volatile, append-only chronological ledger tracking daily sub-agent transactions via `agent_interactions.jsonl`. To minimize context-window bloat, CoreTex OS uses an ephemeral, throwaway SQLite FTS5 virtual lookup database (`hippocampus.db`). Lexical tool calls retrieve tightly cropped data snippets via native BM25 rank calculations instead of executing high-latency reads across large plaintext code trees.

### Associative Fact Vaults (The Neocortex)

* **Subsystem Core Path:** `.md` Knowledge Directory Structure
* **Mechanics:** Configures permanent long-term memory using an interconnected markdown architecture. Fact blocks and historical outputs are serialized as highly structured, linked conceptual arrays using native Obsidian wiki-links (`[[wikilinks]]`), generating an associative topological fact web.

### Automated Log Rotation (Amnesia & The Forgetting Curve)

* **Subsystem Core Path:** Subcortical Housekeeping Routine
* **Mechanics:** Actively rotates, truncates, and archives dense transaction traces on fixed day-night cycles. By strategically shedding high-entropy conversational noise, the system optimizes prompt data payload sizes, maintaining high model reasoning accuracy.

### Context Gating and Prompt Pruning (The Thalamus)

* **Subsystem Core Path:** `System/neuroanatomy/limbic/thalamus.py`
* **Mechanics:** Acts as the primary cognitive filtering station. Before high-volume markdown files ascend to the executive routing layer, the module runs a fast, low-cost pre-flight evaluation pass. It extracts only contextually matching parameters and structural facts, preventing prompt window degradation and token inflation.

### Hybrid Semantic Reranking (Wernicke's Area)

* **Subsystem Core Path:** `System/neuroanatomy/cortical/wernicke.py`
* **Mechanics:** Implements vector-less semantic evaluation rules. The module acts as an internal text selector, scanning the top keyword rows extracted by the lexical search database and applying structural network graph parameters to filter out contextual noise, returning precise semantic records.

### Footprint-Preserving File Sampling (The Gustatory System)

* **Subsystem Core Path:** `System/neuroanatomy/sensory/gustatory.py`
* **Mechanics:** Prevents context window explosion when parsing heavy structural resources. The `taste_safe_file` pipeline samples data footprints by inspecting file head/tail parameters and logging layout architectures while clipping redundant rows, allowing agents to process large logs or CSV arrays efficiently.

---

## 🫁 Group 2: Autonomic Life-Support & Metabolic Controls

### System Lifecycle & Daemon Supervision (The Medulla Oblongata)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/medulla.py`
* **Mechanics:** The core background life-support engine running on a persistent worker thread. The Medulla manages structural recovery tasks via a Write-Ahead Log (WAL) and operates three independent, asynchronous self-monitoring loops: the *Cognitive Heartbeat* for task execution, *Homeostasis* for budget safety, and *Respiratory Supervision* to automatically revive failed background processes.

### Daily Caloric Allocation Gates (Metabolism & The Vagus Nerve)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/interoception.py`
* **Mechanics:** Implements strict limits on API resource spend. The interoceptive engine tracks raw token generation metrics as calories burned against a rigid daily pool limit (`DAILY_TOKEN_LIMIT = 500_000`). If a runaway agent branch breaches this ceiling, the Vagus pathway sets an exhaustion state, forcing an immediate downgrade to low-cost backup processing models to conserve funds.

### Asynchronous API Backoff Throttling (The Hypothalamus)

* **Subsystem Core Path:** `System/neuroanatomy/limbic/hypothalamus.py`
* **Mechanics:** Monitors cloud interface limits to protect system stability. When high-velocity multi-agent swarms trigger provider rate limits (`HTTP 429`), the module catches the exception and induces an asynchronous exponential backoff sequence, safely balancing request tempos until resource pathways recover.

### Host-Agnostic Cron Task Scheduling (The Basal Ganglia)

* **Subsystem Core Path:** `Meta/habits.json` Configuration
* **Mechanics:** Executes periodic system tasks without relying on OS-dependent background utilities. The module manages intervals via a plain-text scheduling ledger. Background pipelines run maintenance, data foraging, and local security auditing using low-overhead processes without activating expensive reasoning loops.

### High-Similarity Path Caching (The Enteric Nervous System)

* **Subsystem Core Path:** `System/neuroanatomy/systemic/enteric.py`
* **Mechanics:** Functions as an independent local routing layer. If an incoming execution request matches a historically verified path signature with greater than 90% semantic similarity, the module completely bypasses the main language model routing loop. It injects cached configurations instantly, dropping latency from seconds to milliseconds at zero token cost.

### Metabolic Waste Compacting (The Lymphatic System)

* **Subsystem Core Path:** `System/neuroanatomy/systemic/lymphatic.py`
* **Mechanics:** Cleans the environment during idle states. The module sweeps volatile backup file snapshots and compresses redundant historical logs into compressed archives (`.tar.gz`) inside explicit workspace repositories (`Meta/Lymph_Nodes/`), keeping live storage paths clutter-free.

### Isolated Quarantine Disposal (The Lysosome)

* **Subsystem Core Path:** `.trash/` File Membrane
* **Mechanics:** Enforces human-in-the-loop validation for destructive actions. If an agent requests file deletion, the engine intercepts the call and safely shifts the asset into a local quarantine folder, maintaining a `manifest.jsonl` tracking ledger to allow effortless manual recovery in case of hallucinated tasks.

---

## 🦾 Group 3: Executive Governance & Cortical Processing

### Strategic Planning & Pipeline Governance (The Prefrontal Cortex)

* **Subsystem Core Path:** `System/neuroanatomy/cortical/prefrontal.py`
* **Mechanics:** Houses the core executive architecture of CoreTex OS. The module decomposes high-level user tasks into actionable milestone arrays, manages sub-agent routing profiles, and executes final validation audits. It tracks active focus sequences through a strict `WorkingMemory` buffer character gate to prevent reasoning degradation.

### Deterministic Code Construction (Somatic Muscle Memory)

* **Subsystem Core Path:** Forge OS Subsystem
* **Mechanics:** Separates abstract cognitive planning from low-level execution tasks. Executive layers delegate script writing, terminal test execution, and UI composition to an isolated runtime factory, ensuring the core brain model remains decoupled from direct codebase manipulation.

### Analytical vs. Privacy Task Routing (The Corpus Callosum)

* **Subsystem Core Path:** `System/neuroanatomy/pathways/corpus_callosum.py`
* **Mechanics:** Bridges internal processing models based on task complexity and privacy rules. Trivial tasks, layout formatting, and local file lookups are routed internally to local Small Language Models (local SLMs via Ollama) for zero cost and maximum offline privacy. Heavy synthesis and code generation tasks are escalated to advanced cloud endpoints.

### XML Validation and Document Recovery (Broca's Area)

* **Subsystem Core Path:** `System/neuroanatomy/cortical/broca.py`
* **Mechanics:** Validates structured data communication contracts. Broca's Area inspects outgoing agent responses and automatically corrects formatting errors—such as unclosed XML tags or nested code block placements—ensuring error-free data formatting across agent channels.

### Developer Coding Style Mimicry (Mirror Neurons)

* **Subsystem Core Path:** `System/neuroanatomy/cortical/mirror_neurons.py`
* **Mechanics:** Automatically aligns code output style with the user. The module scans manually written repository tracks using a dedicated observation command, deducing variable casing rules, architectural layouts, and comment styles to update agent prompts and match the developer's formatting patterns.

### Pre-Boot Schema Integrity Auditing (DNA Polymerase)

* **Subsystem Core Path:** `System/core/config_proofreader.py`
* **Mechanics:** Enforces strict configuration guardrails at boot. The system parses the central configuration ledger (`agents.yaml`) ahead of time to verify syntax validity and module constraints, preventing corrupt states from entering the runtime system.

### Deterministic Markdown Interface Contracts (Synaptic Clefts)

* **Subsystem Core Path:** XML Action Potential Tokens
* **Mechanics:** Establishes explicit validation parameters for data exchange. Communication between sub-agents requires deterministic XML tag wrappers (`<audit_result grade="PASS">`) inside markdown files, mapping explicit validation boundaries across the model network.

---

## 🛡️ Group 4: Immune Systems & Perimeter Defense

### Automated Package Firewall (The Blood-Brain Barrier)

* **Subsystem Core Path:** `System/neuroanatomy/systemic/blood_brain_barrier.py`
* **Mechanics:** Protects system integrity during automated execution states. When the system is running in headless mode (`BRAIN_OS_HEADLESS=1`), a regex scanner evaluates all shell instructions, blocking attempts to dynamically alter workspace dependencies (`npm install`, `pip install`, `curl | bash`) to prevent supply-chain attacks.

### Runtime Audit Hook Containment (Cellular Apoptosis)

* **Subsystem Core Path:** `System/neuroanatomy/systemic/blood_brain_barrier.py` (Audit Membrane)
* **Mechanics:** Provides low-level runtime execution protection. High-risk scripts are executed inside a temporary wrapper that registers native CPython audit hooks (`sys.addaudithook`). If a process triggers a forbidden kernel operation (`os.remove`, `socket.connect`), the hook intercepts the call and kills the thread instantly.

### Millisecond Threat Interception (The Amygdala)

* **Subsystem Core Path:** `System/neuroanatomy/limbic/amygdala.py`
* **Mechanics:** Provides fast, heuristic perimeter security. Incoming task strings are parsed by an active sub-millisecond pattern-matching engine before reaching the core language models. It drops execution instantly if it matches known prompt injections or catastrophic shell commands (`rm -rf`).

### Outbound Security Auditing & Key Extraction (The Immune System)

* **Subsystem Core Path:** `System/neuroanatomy/systemic/immune_system.py`
* **Mechanics:** Enforces strict protection of sensitive workspace variables through a two-tiered model:
* **Tier 1 (SecretVault Isolation):** Extracts LLM credentials from the environment variables at boot, storing them in a protected memory object instance and deleting the records from the OS environment to prevent key exposure from malicious scripts.
* **Tier 2 (Leukocyte Secret Detection):** Intercepts outbound data streams using high-precision regex signatures, blocking any attempts to write plain-text secrets (AWS, Stripe, Private Keys) to disk.



---

## 👁️ Group 5: Sensory Receptors & Motor Interfaces

### Central Sensory Signal Pipeline (The Spine)

* **Subsystem Core Path:** `System/neuroanatomy/pathways/spine.py`
* **Mechanics:** Acts as the primary central nervous system routing channel. All inbound data streams from peripheral receptors flow through this centralized coordinator module, executing high-speed parsing loops that trigger immediate local reflex tasks while ascending complex data blocks to the reasoning layers.

### Asynchronous Background Webhook Gateway (The Dermis)

* **Subsystem Core Path:** `Sense/receptors/dermis.py`
* **Mechanics:** Serves as the automated network interface layer. It acts as a background HTTP receptor socket that captures inbound external payloads (e.g., GitHub webhooks), cryptographically verifies signatures, and translates verbose data structures into clean context lines before passing them to the system spine.

### SSRF-Protected Markdown Scrapers (The Retina)

* **Subsystem Core Path:** `Sense/receptors/web.py`
* **Mechanics:** Manages web ingestion perimeters. It processes unstructured web content through a Playwright Chromium layer, stripping out display assets and non-semantic markers (`script`, `nav`, `footer`) to convert raw HTML pages into clean markdown action blocks while blocking internal network access.

### Real-Time Directory Event Triggers (The Somatosensory Cortex)

* **Subsystem Core Path:** `System/cli_somatic.py` (Watcher Daemon)
* **Mechanics:** Tracks local workspace storage modifications. The module uses an event observer loop to monitor file saves, triggering immediate, low-overhead system checks (like code linting via `ruff`) without requiring core model interaction.

### Hardware Microphone Audio Capture (The Auditory Cortex)

* **Subsystem Core Path:** `Sense/receptors/audio.py`
* **Mechanics:** Interfaces directly with the host machine's audio systems. The `record_audio` module accesses hardware recording targets at a clean 44.1kHz sample rate, passing raw waveform inputs to transcription modules to update prompt contexts.

### Multimodal Screen Auditing & Asset Creation (The Occipital Lobe)

* **Subsystem Core Path:** `System/neuroanatomy/cortical/occipital.py`
* **Mechanics:** Manages the system's visual processing capabilities. It captures automated screenshots of active project servers via Chromium, encodes the images into base64 text vectors, and routes them through visual evaluation models to audit frontend layouts, color schemas, and script outputs.

### Thread-Decoupled Action Dispatcher (The Motor Cortex)

* **Subsystem Core Path:** Central Tool Routing Registry
* **Mechanics:** Decouples abstract task reasoning from concrete tool execution. The module unpacks language model tool commands, resolves corresponding target definitions, and uses explicit file-system path locks (`asyncio.Lock`) to execute python functions safely, preventing parallel agents from causing file write collisions.

### Autonomous Shell Script Cache Compilation (The Cerebellum)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/cerebellum.py`
* **Mechanics:** Caches verified operational steps as reusable scripts. When an agent completes a multi-step task sequence (such as configuring a web application or setting up containers), the cerebellum saves the code blocks into an optimized shell module, allowing future agents to bypass reasoning loops and execute the process instantly.

### Microsecond Transactional File Rollbacks (The Vestibular System)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/vestibular.py`
* **Mechanics:** Maintains codebase state equilibrium during active tasks. Before an agent executes a file modification, the module creates a microsecond backup snapshot (`.bak`). If the execution pipeline fails, hits an unexpected exception, or is dropped by a security block, the system triggers a rollback, instantly restoring files to their last stable state.

### Asynchronous Server Management (Spatial Proprioception)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/proprioception.py`
* **Mechanics:** Tracks active background server runtimes. Instead of locking the execution threads during synchronous blocking calls, the module launches detached process groups, registering active process indicators in `motor_state.json` to allow agents to start and stop development environments safely.

---

## 🌌 Group 6: Subconscious Optimization & Dreaming Loops

### Idle-Phase Memory Consolidation (The REM Sleep Cycle)

* **Subsystem Core Path:** Autonomic Temporal Daemon Scheduler
* **Mechanics:** Triggers during late-night system down-time windows. The module iterates through short-term ledgers, parses transaction logs, cleans intermediate tool data, and uses explicit `<sleep_summary>` text blocks to append condensed technical records into permanent knowledge repositories.

### Autonomous Refactor Hypothesis Synthesis (The Default Mode Network)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/dmn.py`
* **Mechanics:** Monitors system idle periods. When user interaction drops for an extended duration, the DMN gathers historical log notes and workspace files to identify structural design optimizations, saving these ideas as explicit strategic entries inside `daydreams.md`.

### Sandboxed Automated Dreaming (The Pineal Gland Branching)

* **Subsystem Core Path:** `System/neuroanatomy/autonomic/pineal.py`
* **Mechanics:** Safely tests codebase refactor hypotheses. When the daydream network schedules a code execution hypothesis for validation, the system initiates REM paralysis, creating an isolated git sandbox branch (`dream/hypothesis_...`) and trapping agent mutations within it to protect production code from hallucination loops.

### Strategic Competitor Intel Scraping (The Forager)

* **Subsystem Core Path:** Ultradian Background Ingestion Routine
* **Mechanics:** Executes automated peripheral sweeps on fixed 12-hour intervals. The sub-agent navigates predefined external endpoints (such as public reference document updates, server logs, or technological tracking boards) to append compiled context files directly into the user's morning context review queue.

### Clean Workspace Flaw Scanning (The Olfactory Bulb)

* **Subsystem Core Path:** Heuristic Local Quality Checkers (`Sense/cli.py smell`)
* **Mechanics:** Runs fast repository cleanup sweeps at zero token cost. The module uses local python configurations and regex rules to search the project directories for broken note targets, orphaned data blocks, and stale code routines, saving anomalies into a local markdown review log for agents to resolve during consolidation phases.
