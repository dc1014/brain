# 🌌 CoreTex OS Default Mode Network (DMN) & Background Synthesis Model

Most autonomous agent frameworks operate strictly on linear, reactive event loops. When a user stops submitting prompts, the system sits completely frozen—wasting valuable compute idle-time and ignoring the latent structural connections, optimization vectors, and conceptual patterns hidden within its recent execution logs.

CoreTex OS resolves this constraint by implementing a permanent **Autonomic Default Mode Network (DMN)**. Modeled directly after human neurobiology, the DMN functions as a background, non-blocking cognitive synthesis engine that awakens during system idle cycles or simulated sleep states to actively investigate active goals, synthesize insights, and queue proactive tasks for the user.

---

## 🎯 Summary of Token Economics, Traceability, & Goal Alignment

| Subsystem Component | Core Underlying Mechanism | Functional Optimization Strategy |
| :--- | :--- | :--- |
| **1. Dual-Memory Ingestion** | Reads `Core_Beliefs.md` (Epistemology) and `Goals.md` (Teleology). | Ensures the Daydreamer knows *who* you are (preferences, identity) and *what* you are actively trying to achieve. |
| **2. Cognitive Filtering** | Zero-token Python pre-parsing of `Meta/Goals.md`. | Strips out completed tasks and irrelevant domains before feeding the LLM, reducing context token burn by up to 90%. |
| **3. Active Investigation** | DNA-granted investigation tools (`read_safe_file`, `web_search`). | Allows the DMN to actively read workspace files and research the web to gather deep context on stalled goals while you sleep. |
| **4. Proactive Queueing** | Formatted writes to `Meta/Pending_Actions.md`. | The DMN doesn't just think; it decomposes active goals into exact CLI/Agent tasks for the human to approve upon waking. |
| **5. Thread Traceability** | Cryptographic `#goal/UID` injection. | Links every queued action directly back to the Master Goals Kanban board, enabling zero-token state syncing when the task is completed. |

---

## 🔄 The Subconscious Lifecycle: A Biomimetic Deep Dive

When the central orchestrator registers an active workspace pause, or when a user explicitly stimulates the network via the command-line somatic interface (`./ctx sleep`), the DMN initializes a five-phase, highly optimized synthesis routine.

```text
[ Waking Loop Paused ] ---> Trigger Sleep Cycle
                                       |
                                       v
                     [ Phase 1: Dual-Memory Context Extraction ]
                                       |
                                       v
                     [ Phase 2: Cognitive Filtering & Domain Focus ]
                                       |
                                       v
                     [ Phase 3: Active Tool Investigation ]
                                       |
                                       v
                     [ Phase 4: Creative Synthesis & Epiphany ]
                                       |
                                       v
                     [ Phase 5: Proactive Execution Queueing ]
```

### 🗃️ Phase 1: Dual-Memory Context Extraction
To generate actionable insights, the DMN must balance identity with execution. It breaks open two distinct memory silos:
* **Epistemology (`Core_Beliefs.md`)**: The system reads the long-term semantic facts extracted by the Hippocampus (e.g., "The user prefers Pytest," "The user is building a SaaS app").
* **Teleology (`Goals.md`)**: The system reads the hierarchical Kanban board of the user's overarching Directives, Milestones, and Subgoals.
* **Short-Term Memory (`_gather_dream_context`)**: It seamlessly integrates the tail-end of your system performance tracking data, recent command outputs, and the FTS5 SQLite index.

### ✂️ Phase 2: Cognitive Filtering & Token Economics
Feeding a massive, multi-year goal tracker into an LLM context window every night is an economic anti-pattern.
* **The Active Frontline**: Before the LLM turns on, a pure Python script parses the `Goals.md` file line-by-line. It completely drops any tasks marked as completed (`[x]`).
* **Domain Isolation**: It filters out goals that do not match the current operating Domain (e.g., ignoring `PERSONAL` goals if the DMN is waking up in a `PROFESSIONAL` context). The LLM is fed only the hyper-compressed "Active Frontline."

### 🔎 Phase 3: Active Tool Investigation
If the user enabled "Active Daydreaming" during setup, the DMN acts as a proactive researcher.
* **The Investigation Loop**: Seeing an active, uncompleted subgoal, the Daydreamer agent utilizes its active tools (`read_safe_file`, `search_vault`, `web_search`) to read local project files or scrape external documentation, gaining perfect technical context on *why* the goal is stalled and *how* to advance it.

### 🌌 Phase 4: Creative Synthesis
Once context is gathered, the model enters its synthesis phase.
* **The Epiphany**: It synthesizes its strategic insights, architectural proposals, and code refactoring plans into an organized markdown block, appending it under an `## Epiphany` header inside `Meta/DMN/daydreams.md` for the user to review in Obsidian.

### 🧠 Phase 5: Proactive Execution & Teleology Threading
The DMN concludes its cycle by setting up the Medulla (the execution engine) for the next day.
* **Task Decomposition**: It breaks down its Epiphany into 1-2 highly specific, actionable CLI tasks.
* **The Execution Queue**: It appends these tasks to `Meta/Pending_Actions.md` so the user can review and approve them with `ctx approve`.
* **The Traceability Link**: Crucially, it attaches the exact **Teleology Thread ID** (e.g., `#goal/a1b2`) to the pending task. When the system executes this task tomorrow, that ID is passed to the execution log, allowing the Hippocampus to automatically check off the goal on the Kanban board with zero LLM guesswork.

---

## 🛡️ Hardened Security Boundaries & Cognitive Pruning

The Default Mode Network runs autonomously in the background, making strict boundaries essential for maintaining system safety and budget.

* **The Feature Flag Gate**: Active Daydreaming is controlled via `features.json`. If a user opts out of Active Daydreaming, the DNA matrix intercepts the Daydreamer agent during boot and dynamically strips its investigation tools. It reverts to a zero-cost, passive reflection mode.
* **Strict Tool Containment**: Even in Active Mode, the `SUBCONSCIOUS_DAYDREAM` path is tightly sandboxed. The agent possesses *investigative* tools, but is completely stripped of *execution* tools. It cannot run terminal commands, execute code, or overwrite critical system files. It can only read, search, and queue suggestions.
* **Human-in-the-Loop Approval**: The DMN cannot autonomously mutate the active codebase. It queues its intended actions into the `Pending_Actions.md` ledger. A human must explicitly review the Threat Analysis and type `ctx approve` before the system's Prefrontal Cortex is permitted to run the code.
