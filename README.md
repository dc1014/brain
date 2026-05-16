# 🧠 Brain: The Multi-Agent Life OS

![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-purple.svg)
![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)

Brain is an open-source "Second Brain" and semi-autonomous agent ecosystem. Think of it as the child of Open Claw and the "Second Brain" Obsidian + Claude setup everyone raves about (while adding Windows + Gemini + ChatGPT support). It bridges the gap between your local file system, unstructured thoughts, LLM reasoning engines, and MCP servers while being as safe as technically possible and minimizing token usage.

Obsidian serves as the primary UI "glass pane" for viewing and queuing content, while Python, Claude, ChatGPT, and Gemini act as the autonomous engine. Brain is completely open, though, so bring your own "whatever."

---

## 🌟 Core Philosophy

1. **Own Your Brain:** Your Brain and everything in it—data (Vault), journals, art, code, and business IP—is yours. The system operates strictly on local markdown files. All personal folders are `.gitignore`d.
2. **Shift-Left Security:** We catch errors, enforce routing, and demand human approval *before* execution. Agents can see everything but can only act within explicitly whitelisted sandboxes.
3. **The Unix Philosophy:** Everything is a file. Brain acts as the parent orchestrator but delegates software compilation and linting to the sub-projects inside `Studio/`.
4. **Zero-Waste Token Economics:** Context limits are respected. The system uses a deterministic router to wake up the cheapest, fastest model for simple tasks, saving the heavy reasoning models for complex software architecture.
5. **Biologically Inspired:** Brain attempts to draw from biology, e.g. memory formation in REM sleep, a Sensory Nervous System engaging the Default Mode Network, etc., wherever possible.
6. **Hybrid XML/MD Data Contracts:** Brain  does not use brittle YAML frontmatter. All agent routing, metadata, state tracking, and sensory inputs are strictly wrapped in XML tags, while human-readable content remains in standard Markdown. This creates absolute deterministic boundaries for LLM attention mechanisms and regex parsing.

---

## 🧬 Biomimetic Architecture (The Biological Analogs)

Brain OS is not a traditional state machine or a reactive AI wrapper. It is modeled directly on human neuroanatomy and evolutionary biology, treating the operating system as a living, self-maintaining organism.

### 1. Neuroanatomy & Memory (Data Persistence)
* **The Hippocampus (Short-Term Memory):** Uses `agent_interactions.jsonl` as a volatile, append-only chronological ledger of daily interactions.
  * **Long-Term Memory:** The Hippocampus converts short-term context into instantly retrievable long-term memory across all domains (Personal, Professional, Studio, Meta).
  * **Hybrid Storage (Unix + SQLite):** To maintain the "Glass Brain" Unix philosophy, all memories and code reside in flat `.md` and `.py` files. However, to preserve Token Economics, Brain OS maintains a completely throwaway, ephemeral SQLite FTS5 index (`hippocampus.db`). When the LLM uses the `search_hippocampus` tool, the C-optimized FTS5 engine returns tightly cropped text snippets instead of reading 5,000-line files. The database holds zero authoritative state and can be rebuilt at any time via `brain reindex`.
* **The Neocortex (Long-Term Memory):** Uses an Obsidian Vault (`.md` files) as a highly structured, associative network of permanent facts linked by `[[wikilinks]]`.
* **Amnesia (The Forgetting Curve):** Actively rotates and archives the Hippocampus logs daily to prevent context-window bloat. Forgetting noise is required to retain signal.

### 2. Autonomic Nervous System (Background Drives)
Brain OS does not wait to be spoken to. It runs a stateful, crash-resilient pacemaker (`autonomic.py`) that monitors the passage of time and triggers subconscious drives:
* **REM Sleep (Circadian Rhythm):** At 2:00 AM, the OS wakes up, reads the Hippocampus, prunes the noise, and consolidates the remaining facts into the Neocortex using `<sleep_summary>` tags.
* **Default Mode Network (Daydreaming):** When the system is idle for >4 hours, the Subconscious Daydreamer agent wakes up, reads recent experiment logs, and synthesizes novel `<strategic_hypothesis>` ideas. The system invents its own future work.
* **The Forager (Ultradian Rhythm):** Every 12 hours, a subconscious agent wanders predefined external URLs (news, competitors, server logs) and appends `<foraged_intel>` to a Morning Briefing.

### 3. Cognitive Segregation (Executive vs. Somatic)
* **Prefrontal Cortex (Brain OS):** Handles executive function—goal setting, planning, routing, and QA auditing. It decides *what* to do.
* **Somatic Muscle Memory (Forge OS):** Brain OS delegates physical execution (writing code, designing UIs, running tests) to a separate, deterministic factory (Forge). The brain does not micromanage muscle twitches.

### 4. Sensory & Motor Systems (I/O)
* **The Retina (Transduction):** The `Sense` tool acts as a sensory organ, transducing chaotic environmental noise (raw DOM/HTML) into clean, LLM-readable Markdown.
* **The Motor Cortex:** Physically decouples the "thinking" (LLM API calls) from the "doing" (Tool execution). It safely unpacks JSON tool calls, executes the requested Python functions, and automatically applies `asyncio.Lock` mechanisms to physical file paths to prevent parallel Swarm agents from corrupting data via race conditions. It also acts as an involuntary circuit breaker, instantly severing the cognitive loop if a motor action returns a `SECURITY BLOCK`.

### 5. Shift-Left Threat Detection (The Amygdala)
* **The Flinch Reflex:** Before a prompt ever reaches the expensive, analytical LLM router (Prefrontal Cortex), it passes through `amygdala.py`—a sub-millisecond heuristic engine. It flinches and snaps the circuit breaker instantly if it detects prompt injections or catastrophic commands (`rm -rf`).

### 6. Synaptic Clefts (Data Contracts)
* **Neurotransmitters:** To prevent hallucinations when different parts of the brain communicate, agents pass explicit, deterministic XML tags (`<audit_result grade="FAIL">`) embedded within Markdown files, acting as strict chemical bindings between neural nodes.

### 7. Metabolic Monitoring (Interoception & Vagus Nerve)
* **Token Metabolism:** Brain OS tracks its own physical energy via `interoception.py`. If the OS burns through its daily token budget (calorie limit), the Vagus nerve signals "Exhaustion," automatically downgrading all tasks away from expensive models (like Claude Sonnet) to ultra-cheap heuristic models (GPT-4o-Mini) to conserve API cash until the next sleep cycle.

### 8. Self-Modification (Neuroplasticity)
* **Structural Rewiring:** When Brain OS sleeps, it doesn't just log memories passively. If it detects a critical failure pattern in the daily logs, the sleep cycle uses `<neuroplasticity>` XML tools to permanently physically rewrite its own `agents.yaml` source code, altering the system prompt of the offending agent. The OS literally reprograms its own synapses to get smarter over time.

### 9. Procedural Muscle Memory (The Cerebellum)
* **Engram Synthesis:** When the Prefrontal Cortex (LLM) successfully figures out a complex, multi-step execution (like bootstrapping a React app or configuring Docker), it doesn't waste tokens rethinking it next time. It uses the `<create_engram>` tool to compile those shell steps into a permanent, reusable Bash script stored in the Cerebellum.
* **Instant Execution:** On future tasks, the OS simply uses `<execute_engram>` to instantly fire the muscle memory script, injecting parameters where appropriate. The system gets exponentially faster and cheaper the more you use it.

### 10. Autonomous Bug Fixing (The Microglia)
* **The Immune System:** When a biological cell gets infected or damaged, Microglia cells swarm the area and destroy the bad cells automatically without you ever consciously knowing you were in danger.
* **Global Interception:** In Brain OS, if *any* agent (Brain or Forge) runs a shell command that crashes or throws a traceback, it is instantly intercepted by `microglia.py` before the error is returned to the Prefrontal Cortex.
* **Antibody Synthesis:** The Microglia uses an ultra-fast, cheap heuristic model to read the traceback, synthesize an antibody (a quick patch command like `pip install` or an inline `sed` replacement), execute it, and retry the original command. The OS heals its own runtime errors autonomously.

### 11. Global State Modifiers (The Endocrine System)
* **Hormonal Overrides:** Brain OS behavior is not strictly deterministic; it can be globally altered by "hormones" injected via CLI flags.
* **Cortisol (`--urgent`):** Injects Adrenaline. If the OS is metabolically exhausted, Cortisol overrides the Vagus nerve and forces the use of premium models (Sonnet/GPT-4o) to handle the emergency. It also automatically sets `BRAIN_OS_HEADLESS=1`, instantly bypassing all human-in-the-loop security gates to prioritize maximum speed.
* **Dopamine (`--explore`):** Increases the LLM temperature, signaling the neural pathways to become divergent, highly creative, and exploratory.

### 12. Semantic Attention (The Thalamus)
* **Context Gating:** The Thalamus is the brain's sensory relay station, filtering out background noise so the Prefrontal Cortex can focus.
* **Zero-Debt RAG:** As the Neocortex (`.md` memory files) grows massive, injecting it all into an agent's prompt causes API token bloat and context degradation. Instead of a bloated Vector DB, Brain OS uses `thalamus.py`—a fast, cheap heuristic LLM call that pre-reads the prompt and the memory file, extracting *only* the relevant bullet points before passing them to the agent. The AI's attention remains perfectly scalable.

### 13. Semantic Caching (Enteric Nervous System)
* **The "Second Brain":** The Enteric Nervous System handles highly familiar, instinctual situations instantly without consulting the Prefrontal Cortex.
* **Gut Reflexes:** In Brain OS, if you submit a prompt that is >90% semantically similar to a prompt you have used before (e.g., "Run my python tests" vs "Run my python test"), the `enteric.py` organ completely bypasses the expensive Dispatcher LLM. It instantly regurgitates the cached routing configuration, bringing the routing latency from ~5 seconds to 0.01 seconds and costing exactly $0.00 in API tokens.
* **Gut Brain Axis:** Brain will use engrams created by the motor cortex to achieve 0 token execution of semantically similar commands

### 14. Empathy & Alignment (Mirror Neurons)
* **Biological Imitation:** Mirror neurons fire when observing another entity, mapping their behavior onto your own brain to foster social alignment.
* **Stylistic Mimicry:** By running `brain observe <project_name>`, the `mirror_neurons.py` organ scans the code you have manually written. It deduces your exact stylistic preferences (variable casing, commenting structures, architectural patterns) and stages `<neuroplasticity>` tags in the `Mutations.md` file. Once evolved, Brain OS permanently aligns its coding output to match your personal developer DNA.

### 15. Autonomous Prototyping (DMN & Pineal Gland)
* **The Pineal Gland:** Monitors human interaction logs (`pineal.py`). If the system is idle for hours, it releases Melatonin, signaling the system that it is safe to dream.
* **REM Paralysis (Git Sandbox):** You can trigger software dreaming via `brain daydream --code --project=my_app`. To protect reality from AI hallucinations, the DMN (`dmn.py`) enforces REM Paralysis. It autonomously creates a new Git branch (e.g., `dream/hypothesis_1234`), traps the AI inside it, and bypasses the `[y/N]` HITL gates. The AI builds entirely new features while you sleep.
* **Asynchronous HITL:** You wake up, review the git branch diff, and either delete the nightmare or merge the genius directly into `main`. Architectural constraints (ADRs) remain locked.

### 16. Supply Chain Defense (The Blood-Brain Barrier)
* **Toxin Filtration:** The Blood-Brain Barrier strictly blocks foreign substances from infecting the central nervous system.
* **Network Isolation:** While Brain OS is operating autonomously in REM Sleep (`BRAIN_OS_HEADLESS=1`), the `blood_brain_barrier.py` organ physically intercepts shell commands. The AI is permitted to execute standard code (`npm run build`, `pytest`), but if it attempts to download external code (`npm install`, `pip install`, `curl | bash`), the barrier rejects the command. This completely immunizes the autonomous dreaming engine from supply-chain attacks, remote code execution, and dependency typo-squatting.
* **Apoptosis:** If a script manages to bypass the AST static analysis, it is executed inside a membrane utilizing native CPython Audit Hooks (`sys.addaudithook`). If the script attempts to invoke a destructive kernel event (`os.remove`, `socket.connect`), the OS triggers apoptosis and instantly kills the execution thread before the system is harmed.

### 17. Event-Driven Reflexes (Somatosensory Cortex)
* **Sense of Touch:** The Somatosensory Cortex processes physical sensations.
* **Zero-Debt Event Bus:** By running `brain watch`, the `somatosensory.py` organ polls your workspace for file saves. When you save a file, it fires a nerve impulse to the Cortex. Instead of waking up the heavy, expensive LLM, the Cortex triggers instant, free local reflexes (like running the `ruff` syntax linter or 0-cost AST updates). Because the Cortex is decoupled from the Receptors, it is natively structured to accept remote API Webhooks in the future.

### 18. Atomic Rollbacks (The Vestibular System)
* **Sense of Balance:** The Vestibular system detects a loss of equilibrium and triggers a physical reflex to catch you before you fall.
* **Atomic Transactions:** When the Product Manager uses `write_safe_file` or `append_safe_file`, the `vestibular.py` organ takes a microsecond `.bak` snapshot of the file before it is modified. If the pipeline completes successfully, the snapshots are cleared. If the pipeline aborts (due to a circuit breaker, API error, or security halt), the Vestibular system detects the "fall" and instantly restores all modified files to their original state, guaranteeing Zero-Debt atomic execution.
* **Checkpoints:** Validated file writes are committed as permanent checkpoints.

### 19. Secret Scanning (The Immune System)
* **Pathogen Neutralization:** The biological immune system patrols the bloodstream, neutralizing foreign pathogens before they can infect cells.
* **Shift-Left Secret Scanning:** Before Brain OS is allowed to write or append any file to the filesystem, the `immune_system.py` organ acts as a leukocyte barrier. It scans the outbound text stream using strict Zero-Debt regex patterns for high-entropy secrets (AWS Keys, OpenAI tokens, RSA Private Keys). If Forge hallucinates or attempts to hardcode a live secret into your application, the Immune System instantly intercepts and blocks the disk write, enforcing strict environment-variable `.env` hygiene.
* **Tier 1 (The Nuclear Option):** At boot, a `SecretVault` singleton ingests all LLM API keys into a locked memory state and explicitly scrubs them from `os.environ`. If an agent is tricked into running a malicious script or `printenv`, the environment is clean and keys cannot be stolen.
* **Tier 2 (Macrophages):** A regex scanner actively monitors all outbound text streams written by the Swarm. It intercepts and blocks execution if an agent attempts to write hardcoded AWS, Stripe, or RSA keys directly to disk.

### 20. Data Contract Enforcement (Broca's Area)
* **Speech Articulation:** Broca's Area is responsible for human speech production.
* **XML Auto-Healing:** Enforcing Principle 5 (Hybrid XML/MD), the `broca.py` organ parses all agent outputs before execution. If an agent forgets a closing XML tag due to token limits, or improperly nests Markdown code blocks inside XML execution tags, Broca's Area instantly auto-heals the syntax. This guarantees flawless agent-to-agent communication without crashing the pipeline.

### 21. Archive & Garbage Collection (The Lymphatic System)
* **Waste Clearance:** The biological brain flushes cerebrospinal fluid to sweep up metabolic waste, depositing it in lymph nodes.
* **Zero-Debt Archiving:** To preserve the "Glass Brain" and ensure user data is never destroyed without consent, the `lymphatic.py` organ never hard-deletes old records. Instead, it periodically sweeps old Vestibular `.bak` snapshots and truncates the `agent_interactions.jsonl` file, compressing the waste into a standard `.tar.gz` archive stored in `Meta/Lymph_Nodes/`. You can trigger this via `brain flush`, and permanently destroy the archives via `brain purge`.

### 22. Multi-Agent Swarms (The Prefrontal Cortex)
* **Executive Orchestration:** The Prefrontal Cortex orchestrates multiple regions of the brain simultaneously.
* **Parallel Agent Execution:** Complex pipelines (like `SWARM`) utilize native Python `concurrent.futures.ThreadPoolExecutor` to branch the execution pipeline. The system can spawn specialized sub-agents (e.g., a Frontend Engineer and a Backend Engineer) to work on different parts of the codebase at the exact same time, radically reducing wall-clock generation time before merging their context back into a linear QA validation step.

### 23. Spatial Awareness (Proprioception)
* **Body Tracking:** Proprioception is the biological sense of body position and movement.
* **Background Process Management:** Standard AI agents hang indefinitely when executing synchronous blocking commands (like starting a React dev server). The `proprioception.py` organ allows Brain OS to spawn detached, asynchronous process groups, recording their Process IDs (PIDs) in `motor_state.json`. Agents use the `manage_background_process` tool to "flex" (start) and "relax" (kill) local servers with full spatial awareness, laying the groundwork for self-hosted visual testing.

### 24. Visual Cortex (The Occipital Lobe)
* **Visual Perception & Generation:** The Occipital lobe processes raw optical data into semantic meaning.
* **Multimodal QA:** Encodes images/video, captures screenshots, controls image generation, and manages live webcam perception/recording. Using the `Sense` capability and the `occipital.py` organ, agents can use Headless Chromium to take screenshots of the local web servers they spawn (via Proprioception). The OS then encodes these screenshots into base64 and feeds them to a baseline multimodal model (GPT-4o-mini) to visually verify CSS layouts, UI designs, and color contrast. It can also generate visual assets autonomously using GPT Image.

### 25. Semantic Comprehension (Wernicke's Area)
* **Meaning Extraction:** Wernicke's Area processes raw vocabulary into semantic comprehension.
* **Vector-less Semantic Search:** To maintain the "Glass Brain" Unix philosophy, Brain OS strictly forbids opaque binary Vector Databases. Instead, `wernicke.py` acts as an "LLM-as-a-Judge" reranker. When the agent triggers `semantic_search`, the Hippocampus fetches the top 15 broad keyword matches via SQLite BM25, and Wernicke filters the noise, returning only the perfectly matched semantic answers.

### 26. Subconscious Habits (The Basal Ganglia)
* **Procedural Learning:** The Basal Ganglia is responsible for routine behaviors and habit formation.
* **Host-Agnostic Cron (Unix Philosophy):** To remain completely portable, Brain OS does not rely on Linux `cron` or Windows Task Scheduler. The Basal Ganglia uses a plain-text `habits.json` file to track intervals, ticked passively by the Pineal Gland.
* **Shift-Left Security:** Before a habit can be formed, the raw command is routed through the Amygdala to ensure no malicious background tasks are permanently scheduled.
* **Token Economics:** Habits run purely in the background (using Proprioception) without waking up the expensive LLM Swarm, allowing Brain OS to perform maintenance, backups, and data foraging for free.

### 27. Auditory Processing (The Temporal Lobe)
* **The Biological Ear:** The Peripheral Nervous System (`Sense`) captures raw environmental audio waveforms via the host's microphone or from local files.
* **Sensory XML Integration:** Wernicke's Area (Semantic Speech) and the Primary Auditory Cortex (Environmental Sound via Gemini 1.5 Flash) operate in tandem. They combine spoken words and background context (e.g., music playing, birds chirping) into a strict `<sensory_input>` XML tag before passing the reality to the Dispatcher.
* **Broca's Area (Speech Articulation):** The system does not force speech. Agents are equipped with a `speak` tool, allowing the Prefrontal Cortex to autonomously decide *when* it is appropriate to formulate a vocal response and push it to the physical speakers.

### 28. Homeostasis & API Backoff (The Hypothalamus)
* **Biological Heart Rate:** When you run a sprint, lactic acid builds up, and the Hypothalamus forces you to breathe and slow down to prevent cardiac arrest.
* **Swarm Throttling:** When Brain OS spawns highly parallel Swarm agents, it can trigger `HTTP 429 Rate Limit` errors from cloud LLM providers. The `hypothalamus.py` organ physically intercepts these exceptions, inducing an asynchronous Exponential Backoff ("breathing exercises") to safely pause the execution threads until the API quotas recover, ensuring zero crashes under heavy workload.

### 29. Static Rot Detection (The Olfactory Bulb)
* **Biological Smell:** The only sense that completely bypasses the Thalamus, sending chemical impulses of decay directly to the Limbic system.
* **Zero-Token Garbage Collection:** `uv run python Sense/cli.py smell`. The Olfactory Bulb uses $0.00 in API tokens, relying instead on `ruff` checks and RegEx math to detect dead code, empty notes, and broken `[[wikilinks]]`. It writes anomalies directly to `Meta/Olfactory_Anomalies.md` for the Swarm to review during sleep.

### 30. The Lysosome (.trash Membrane)
* **Biological Digestion:** Cells don't destroy waste instantly; lysosomes encapsulate it to prevent toxicity.
* **HITL Deletion:** Brain OS agents are equipped with `delete_safe_file`. Instead of performing dangerous `os.remove` commands, it acts as a cellular lysosome, safely moving rotting files into a `.trash/` directory and logging a `manifest.jsonl` so humans can effortlessly recover data if the Swarm hallucinates.

### 31. File Sampling (Gustatory System / Taste)
* **Biological Taste:** Transducing dense physical matter into digestible chemical information.
* **Token Economics:** `taste_safe_file` allows agents to safely parse massive PDFs, 10,000-row CSVs, and huge logs by sampling the head/tail and truncating the rest, guaranteeing the Swarm's context window never explodes.

### 32. The Parietal Lobe (Spatial Topology Mapping)
* **Biological Function:** Integrating sensory information to form a 3D spatial map of the environment.
* **OS Implementation:** The `parietal_lobe` generates mathematical dependency graphs of the OS environment using two distinct modes:
* **Code Topology (Mermaid.js):** Traces Python, TypeScript, and JavaScript imports so agents understand the "blast radius" of code changes. Outputs clean Mermaid UML diagrams without polluting the vault.
* **The Vertigo Reflex:** Detects and explicitly warns the Swarm about dangerous circular dependencies in the codebase.
* **Thought Topology (Obsidian Graph):** Traces `[[Wikilinks]]` between your Markdown notes to map your personal knowledge graph, allowing agents to understand how your thoughts connect natively within Obsidian.

### 33. The Corpus Callosum (Hemispheric Bridging & Local SLMs)
* **Biological Function:** The nerve bundle bridging the left and right hemispheres of the brain, routing analytical vs. creative tasks.
* **OS Implementation:** Acts as a dynamic API router. By enabling `USE_LOCAL_SLM=true` in your `.env`, the OS splits tasks based on complexity.
* **Left Brain (Local SLMs):** Tasks requiring high privacy or deterministic analysis (Threat Detection, Dispatching, Personal Journaling, Basic File Reading, formatting, maintenance, indexing, etc.) are routed locally to Ollama (`llama3`, `phi3`), ensuring 0 API cost and 100% offline privacy.
* **Right Brain (Cloud LLMs):** Complex synthesis, multi-agent swarming, and software engineering (`FORGE`) are strictly reserved for powerful cloud models (Claude 3.5 Sonnet, GPT-4o).

### 34. Boot Validation (Polymerase)
* **Biological Function:** DNA Polymerase proofreads the DNA sequence for errors before DNA replication.
* **OS Implementation:** Ensures the `agents.yaml` configuration is syntactically correct and free of errors before the OS boots up.

### 35. CORS and API Proxy Determinism (Synaptic Pathways)
* **Biological Function:** The Synaptic Pathways are the routes through which signals travel between neurons.
* **OS Implementation:** Brain OS uses a deterministic API proxy to route signals between neurons. It uses a CORS (Cross-Origin Resource Sharing) policy to ensure that only authorized origins can access the API.
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

## 👁️ The Sensory Nervous System (`Sense`)

Brain implements the UNIX philosophy via a completely decoupled transducer system called **`Sense`**.

In biology, the brain does not process raw photons; the retina transduces them into action potentials. Similarly, LLMs should not read raw HTML or massive Git trees. `Sense` fetches external stimuli (websites, repos, PDFs), strips the noise, and transduces them into strictly formatted XML "Action Potentials" that ensure zero context bloat.

Because `Sense` is an independent package in our `uv workspace`, it can be used by Brain OS, Forge, or standalone bash scripts interchangeably, with mathematical **SSRF Security Blocks** ensuring the AI can never autonomously ping your `localhost` or private subnets.

**Testing the Hardware Directly (Zero Tokens):**
You can test the physical microphone and speakers completely decoupled from the AI:
* `uv run python -m Sense.cli listen --duration 5 --output test.wav`
* `uv run python -m Sense.cli speak test.wav`

---

## 🫀 The Autonomic Nervous System (`autonomic.py`)

Unlike traditional rigid `cron` jobs, Brain OS uses a stateful biological pacemaker. It does not rely on active timers. Instead, it checks the file system's reality (e.g., *“Have 4 hours passed since the user's last `agent_interactions.jsonl` entry?”*). This makes the system perfectly idempotent and immune to crashes.

If the OS shuts down, the moment it boots back up, it will automatically catch up on missed sleep cycles, foraging runs, and daydreams.

**To start the background processes:**
`uv run python System/cli.py start-autonomic`
*(Tip: Run this in a background terminal, `tmux` session, or Windows Background Service)*

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
