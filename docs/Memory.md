# 🧠 CoreTex OS Memory Architecture & Synaptic Consolidation Model

Most autonomous agent frameworks treat context as an unmanaged history array or rely entirely on slow, expensive vector lookups that suffer from context drift, drop historical technical depth, or inflate API bills.

CoreTex OS resolves this constraint by implementing a **5-Tier Biomimetic Cognitive Memory Stack**. Information flows from high-frequency volatile runtime buffers through structural reranking algorithms, culminating in low-entropy technical documentation archives consolidated during sleep cycles.

---

## 🎯 Summary of Token & Memory Architecture Controls

| Cognitive Memory Layer | Core Storage Subsystem Model | Preservation & Optimization Strategy |
| --- | --- | --- |
| **1. Working Memory** | Volatile high-frequency RAM buffer inside `working_memory.py`. | Dynamically intercepts arrays exceeding 12,000 characters and executes a recursive **Rolling Context Compression** to prevent context amnesia or token death spirals. |
| **2. Short-Term Memory** | SQLite FTS5 Virtual Table Indexing inside `hippocampus.py`. | Replaces slow, expensive vector model search requests with keyword ranking and extracts precise snippet text windows. |
| **3. Knowledge Topology** | Relational backplane mapped to `.brain/graph_state.json`. | Parses explicit note connection syntax and uses an ACC monitoring hook to block file writing if looping faults occur. |
| **4. Episodic Memory** | Thread-safe, lock-protected JSONL stream inside `episodic.py`. | Registers permanent historical completion entries to track workflow success and optimize prioritization trees. |
| **5. Synaptic Vault & Core Beliefs** | Persistent Markdown document logs and `Core_Beliefs.md` across system folders. | Runs background sleep cycles to clean runtime logs, archive technical depth, and extract persistent semantic beliefs (e.g., framework preferences) for zero-shot personalization. |

---

## 🧭 The Cognitive Memory Processing Hierarchy

When a process executes or telemetry is generated, data flows down through the following cognitive storage boundaries:

```text
    [High-Frequency Sub-Agent Actions & Telemetry Logs]
                             │
                             ▼
         ┌──────────────────────────────────────┐
         │ 1. Cortical Working Memory Buffer    │  <-- Rolling Context Compression (12k Wall)
         └───────────────────┬──────────────────┘
                             │
                             ▼
         ┌──────────────────────────────────────┐
         │ 2. Lexical Short-Term Search Index   │  <-- SQLite FTS5 BM25 Ranking
         └───────────────────┬──────────────────┘
                             │
                             ▼
         ┌──────────────────────────────────────┐
         │ 3. Relational Knowledge Graph        │  <-- ACC Stress-Gated Topologies
         └───────────────────┬──────────────────┘
                             │
                             ▼
         ┌──────────────────────────────────────┐
         │ 4. Autobiographical Episodic Ledger  │  <-- Thread-Safe Write-Ahead JSONL
         └───────────────────┬──────────────────┘
                             │
                             ▼
  ===========================▼======================================================
  💤 THE DEEP CONSOLIDATION SUBCORTEX (Asynchronous Sleep & Dream Cycles)
  ==================================================================================
                             │
                             ▼
         ┌──────────────────────────────────────┐
         │ 5. Synaptic Vault & Belief Injection │  <-- Low-Entropy Domain Documenting
         └──────────────────────────────────────┘


```

---

## 🛠️ Deep-Dive Analysis of the 5 Memory Layers

### 1. Cortical Working Memory (The Semantic Compressor)

* **Source Subsystem Location:** `System/neuroanatomy/cortical/working_memory.py`
* **Primary Interface Class:** `WorkingMemory` & `compress_message_array`
* **Storage Latency Model:** Volatile, high-frequency runtime memory arrays.

#### Implementation Mechanics

Active sub-agent execution steps and JSON tool outputs are passed directly into the execution history array. Unlike legacy agents that suffer from "amnesia" by silently discarding older messages (FIFO), CoreTex OS evaluates the active token footprint of the entire conversation.

When total logs cross the 12,000 character threshold, `compress_message_array()` executes. It fires an asynchronous background call using a fast, high-efficiency model (e.g., `gemini-2.5-flash`) to summarize the historical middle-nodes of the conversation.

The processor strips away conversational filler, flattens synthetic tool results, and consolidates the execution stream into a compact bulleted list. This **Working Memory** block is then seamlessly injected directly into the active User prompt. This grants the agent a mathematically infinite, rolling context window while preserving strict API role-sequence compliance (Anthropic/OpenAI) by keeping the execution head and tail untouched.

---

### 2. Lexical Short-Term Recall (SQLite FTS5 Index)

* **Source Subsystem Location:** `System/neuroanatomy/limbic/hippocampus.py`
* **Primary Targets:** `_get_conn()`, `encode_memory()`, `recall_memory()`
* **Storage Latency Model:** Local database engine with virtual full-text mapping.

#### Implementation Mechanics

Rather than spending tokens or processing time querying external vector database models for project text file analysis, CoreTex OS maps localized storage queries through a virtualized indexing engine. At boot or reindex sweeps, workspace directories (`Studio`, `Meta`, `Personal`, `Professional`) are scanned for valid code extensions (`.py`, `.md`, `.json`, `.ts`). Content payloads are written straight into a local SQLite virtual data configuration:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS memories
USING fts5(filepath, content, timestamp UNINDEXED);


```

When `recall_memory` executes a lookup query, Pass 1 computes fast lexical text matches via the database engine's native BM25 rankings: `(bm25(memories) * -1.0) AS score`.

Pass 2 sends these matches to Wernicke's translation module to adjust positions based on relational graph connection densities. Pass 3 extracts precise contextual snippets using SQLite's native text highlighters: `snippet(memories, 1, '[MARK] ', ' [/MARK]', '...', 25)`. This ensures prompt context blocks are constrained to target code snippet lines, eliminating raw file dumps.

---

### 3. Relational Knowledge Topology (The Supervised Graph Backplane)

* **Source Subsystem Location:** `System/neuroanatomy/limbic/hippocampus.py`
* **Primary Target Classes:** `GraphBackplane`, `SupervisedGraphBackplane`
* **Storage Latency Model:** Serialized network topology map index file located at `.brain/graph_state.json`.

#### Implementation Mechanics

The system extracts explicit cross-document connections by parsing markdown files using custom-compiled regex matching operations:

```python
self.link_regex = re.Pattern = re.compile(r"\[([a-zA-Z_0-9\-]+)::\[\[([^\]]+)\]\]\]")


```

This syntax explicitly extracts custom relationship structures across system notes (e.g., `[resolves::[[daydreams]]]`).

To prevent technical debt or loop pollution within long-term relational structures, the `SupervisedGraphBackplane` routes all compilation operations through an **Anterior Cingulate Cortex (ACC)** monitoring hook. Before writing structural link maps to disk, `supervised_rebuild` prompts the ACC to evaluate the recent context buffer history. If the ACC detects stuck loops or repetitive tool failure states, it locks further writing via a security exception:

```python
if tension_report.get("action") == "FORCE_STRATEGY_SHIFT":
    raise RuntimeError("Graph write suspended by Anterior Cingulate Cortex due to high tension...")


```

This protects the centralized knowledge database, keeping the graph architecture unpolluted until the system resolves the execution fault.

---

### 4. Autobiographical Episodic Ledger

* **Source Subsystem Location:** `System/neuroanatomy/limbic/episodic.py`
* **Primary Targets:** `encode_episode()`, `recall_recent_episodes()`
* **Storage Latency Model:** Permanent flat-file JSONL appending stream mapped to `Meta/autobiography.jsonl`.

#### Implementation Mechanics

Every time a complex multi-agent orchestration loop signs off its processing goals, `encode_episode()` compiles a comprehensive lifecycle entry tracking the objective, task array, and pipeline outcome.

To support heavy parallelization across asynchronous execution loops, all write operations are wrapped within a thread-safe file mutex lock via `BiologicalLock(str(MEMORY_FILE))`. This ensures data consistency by blocking concurrent processes from causing file access collisions during append spikes.

The moment the entry is written to disk, it executes a dopamine reinforcement check within the reward center (`process_dopaminergic_reward(objective, outcome)`) to optimize future agent prioritization trees based on past outcomes. Active orchestration pipelines call `recall_recent_episodes(limit=5)` to inject recent autobiographical records into current prompt windows, helping the system learn from past failures and prevent repeating execution errors.

---

### 5. Synaptic Consolidation (Long-Term Domain Documentation & Core Beliefs)

* **Source Subsystems:** `System/neuroanatomy/limbic/hippocampus.py` & `System/neuroanatomy/autonomic/dmn.py`
* **Primary Targets:** `_encode_short_term_memory()`, `_extract_and_update_beliefs()`, `trigger_daydreams()`
* **Storage Latency Model:** Permanent Markdown files (`Core_Beliefs.md` and domain memories) organized across specific system directories.

#### Implementation Mechanics

During low-load phases, idle intervals, or manual `sleep()` sequences, the engine initiates long-term memory consolidation via `consolidate_short_term_memory()`. The subcortex processes these memories through a structured three-pass routine:

* **Log Foraging & Sorting:** Pass 1 walks directory paths to locate all `agent_interactions.jsonl` files. It grabs the last 50 transactions and classifies them into explicit functional domains (e.g., `STUDIO`, `META`, `PERSONAL`, `PROFESSIONAL`).
* **Semantic Belief Extraction:** Pass 2 isolates user prompts and system responses to extract persistent rules. It distills facts like framework preferences, directory structures, and environment goals, appending them to `Meta/Core_Beliefs.md`. These "Beliefs" are dynamically injected into the system prompt upon subsequent reboots to achieve zero-shot personalization.
* **Low-Entropy Vault Archiving:** Pass 3 strips out transient tool error histories, condensing the logs into a technical bulleted summary highlighting architecture updates and project changes. Core system summaries append to `Meta/global-memory.md` while unique domain records append to `{Domain}/{domain_name}-memory.md`.

Concurrently, the **Default Mode Network (DMN)** triggers background reflection cycles via `trigger_daydreams()`. It crawls through historic system errors in `medulla.log` alongside randomized files across user markdown vaults to identify non-obvious optimizations. These optimizations are recorded as insights within `daydreams.md`, and the system can automatically schedule execution code changes under isolated git branches to evaluate them safely.

---

## 🧬 Memory Encoding & Retrieval Flow

### 1. The CAS Gatekeeper & Event-Driven Indexing

Instead of running an expensive $O(N)$ full-directory crawl across the vault, the Hippocampus utilizes incremental event-driven indexing hooked into the Somatosensory watcher daemon. Before a file is parsed or analyzed, its content is hashed (`sha256`). If the hash matches the SQLite `file_hashes` tracking registry, the system immediately aborts the parsing pipeline, skipping regex checks and saving massive CPU cycles.

### 2. The Ripgrep Engine & Context Window Protection

When an agent executes a global search (`global_text_search`), CoreTex OS completely bypasses Python's internal memory allocation limits by dropping into a native `ripgrep` (`rg`) subprocess.

To protect the LLM from token degradation when retrieving massive files, the Hippocampus employs a **Hybrid Illusion**. If the Ripgrep search hits a massive file, Python silently intercepts the output and stitches the pre-computed Semantic Sidecar summary directly to the top of the search result. The agent gains total technical omniscience without ever flooding its context window.

### 3. Sleep Cycle Synaptic Consolidation

During inactive idle intervals, or system shutdown sequences, the engine initiates long-term memory consolidation via `consolidate_short_term_memory()`. The subcortex processes these memories through a structured routine:

* **Semantic Compaction Sweep:** The daemon scans the FTS5 index for any "heavy" files (>3,000 characters) that have been modified. It uses a low-cost, high-speed model (like `gemini-2.5-flash` or `gpt-4o-mini`) to compress the file into a dense, 2-3 sentence technical abstract, storing it safely in the `semantic_cache` sidecar without corrupting the user's local Obsidian files.
* **Belief Extraction:** Passive extraction of long-term semantic rules and workspace architectures into `Core_Beliefs.md` for permanent agent personalization.
* **Low-Entropy Text Distillation:** It strips out transient tool error histories, temporary variables, and intermediate text filler, condensing the logs into a technical bulleted summary highlighting architecture updates and project changes.
* **Vault Archiving:** This long-term memory summary is appended directly into targeted Markdown files across specific workspace subfolders (`Meta/global-memory.md`).

```

```
