# Brain OS Token Economics & Metabolic Infrastructure

Most autonomous agent architectures treat tokens as an abstract billing concern, running execution scripts continuously until an API key wallet runs dry or a rate limit forces a hard crash. Brain OS models token management through **Autonomic Metabolic Interoception**.

By treating token windows and API requests as a scarce biological resource, the system monitors, compresses, and gates data ingestion across the entire processing stack—spanning the sensory perimeter, cortical working memory, and core brainstem routing.

---

## 🎯 Summary of Token Optimization Controls

| Subsystem Component     | Control Feature                                    | Token Preservation Strategy                                                                                                  |
| ----------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **`interoception.py`**  | Daily Token予算 Perimeter (`500k` Cap)               | Hard physical lock halts execution when limit is breached, preventing financial overruns from agent loop faults.             |
| **`medulla.py`**        | Contextual Orchestration Specificity (COS) Arbiter | Routes trivial operations to lightweight, cost-effective models while reserving expensive models for high-intensity tasks.   |
| **`working_memory.py`** | Cortical 12,000-Character Wall & Compressor        | Flushes runtime log arrays by condensing detailed execution steps into dense, low-entropy technical bullet points.           |
| **`hippocampus.py`**    | SQLite FTS5 Indexed Lookups & Re-Ranks             | Bypasses expensive multi-pass model vector searches, injecting precise context windows rather than whole files into prompts. |
| **`Sense / Receptors`** | Perimeter Filtering & Payload Truncation           | Limits incoming unstructured peripheral data text blocks at the socket line before they can reach reasoning layers.          |

---

## 1. The Daily Caloric Budget (Metabolic Interoception)

Brain OS models raw token usage as systemic "calories burned". This allocation is governed by the interoceptive framework:

* **Hard Perimeter Ceiling:** The system establishes a baseline cap of `DAILY_TOKEN_LIMIT = 500_000` tokens per day.
* **Write-Ahead Ledger Logging:** Every cognitive action records telemetry down to `logs/metabolism.json` via `log_metabolism(tokens)`.
* **The Exhaustion Latch:** The moment the total token consumption equals or exceeds the ceiling, the system sets `exhausted = True`. This state acts as an immediate physical lock, withholding further execution clearance from cognitive pathways.
* **Temporal Homeostatic Resets:** The metabolism auto-resets when the calendar date changes (`data.get("date") != today`). This mismatch clears `tokens_burned` back to zero and flips `exhausted` to false, restoring the system's full pool for the new day.

---

## 2. Contextual Orchestration Specificity (COS) Arbiter

To protect the daily budget from being exhausted by trivial tasks, the brainstem (`MedullaOblongata`) processes incoming workloads using a specificity-weighted evaluation engine rather than a binary on/off toggle.

* **Predictive Command Scoring:** When a command enters the queue, `calculate_specificity_score(command_string)` scores its expected resource footprint. It adds a base score of 10, then flags heavy execution pipelines (`execute_pipeline` / `dispatch_task` add +40), browser orchestration operations (`playwright` / `chromium` add +30), and recovery states (`recovery` / `acc` add +25).
* **Tiered Resource Allocation:** Scores are mapped directly to runtime environments via `allocate_orchestration_tier(score)`:
* **Scores >= 70:** `ORCHESTRATION_CRITICAL`
* **Scores >= 40:** `ORCHESTRATION_STANDARD`
* **Scores < 40:** `ORCHESTRATION_MINIMAL`


* **The Minimalist Active Profile:** Trivial system tasks and standard heartbeat checks are confined to the `com.brainos.minimal_ready` profile boundary. This ensures the system runs on lightweight models (like local SLMs) by default, preserving premium, high-cost tokens for advanced reasoning scenarios.

---

## 3. Cortical Buffer Gating & Lossless Semantic Compression

As an active task pipeline executes, the Prefrontal Cortex framework (`WorkingMemory`) uses explicit constraints to manage the context window, preventing prompt bloating and model attention degradation.

* **Structured Attention Trees:** Raw sub-agent output logs and terminal telemetries are encapsulated inside explicit XML-style tags (`<activity_node>`, `<raw_telemetry>`, `<actions_taken>`). This targets model attention specifically on execution facts, minimizing structural token noise.
* **The Character Footprint Wall:** The volatile buffer monitors its cumulative footprint against a strict character length gate:
```python
self.compression_threshold_chars = 12000

```


* **Zero-Temperature Text Distillation:** When length breaches this wall, `compress_if_bloated()` executes. It feeds the accumulated activity log into a fast consolidation model operating at `temperature=0.0`. The model discards all conversational text filler and synthesizes raw logs into a highly technical, dense bulleted list of "Established Facts" and "Current State" wrapped inside `<summary_update>` blocks.
* **Volatile Memory Flush:** This compact summary updates the long-term `established_facts` tracking cache, and the high-frequency log array is completely cleared. This loop stops linear context explosion, ensuring prompt inputs remain tightly bounded.

---

## 4. Epistemic Lookahead Context Pruning

When an agent needs to recall past tasks or project context, reading entire files or running multi-pass embedding lookups consumes substantial processing time and tokens. The Hippocampus (`hippocampus.py`) optimizes this via a localized virtual indexing architecture.

* **SQLite FTS5 Truncation:** Instead of generating vector embeddings for every local workspace file modification, the Hippocampus drops codebase files directly into an internal SQLite FTS5 table. Keyword retrieval matches documents instantly using native BM25 rank calculations, bypassing model-based semantic search calls.
* **Graph-Boosted Lookahead Filtering:** Lexical search results are cross-referenced with Wernicke's translation layer via `rank_graph_boosted_results`. Wernicke parses the system's serialized relational network graph state file to evaluate node connection density. Files with higher structural connection density receive an evaluation boost, bubbling up relevant information without packing unnecessary files into the active prompt workspace.
* **High-Precision Snippet Extractors:** Rather than injecting entire code files or raw scripts into the context window, SQLite uses the `snippet()` function to isolate targeted, matching context windows highlighted by custom delimiter tokens (`[MARK] ... [/MARK]`). This ensures prompt inputs are limited to precise, relevant code lines.

---

## 5. Sensory Ingestion Gating (The Sense Membrane)

Unchecked streaming data from peripheral receptors (like web page scrapers, audio processing devices, or vision streams) can introduce large amounts of unstructured text noise, threatening token economics. The `Sense` module mitigates this at the ingestion perimeter:

* **Inert Sensory Encapsulation:** Raw external signals are neutralized via `scrub_payload`. This replaces problematic character chains and locks text payloads inside static read-only token boundaries (`[[UNVERIFIED SENSORY STIMULUS]] ... [[END SENSORY INPUT]]`). This structure enforces rigid token alignment, preventing incoming web data or logs from masquerading as system instructions and causing expensive reasoning inflation.
* **Perimeter Payload Truncation:** Subsystems (such as the FastAPI-driven web interface layer `DermisAbstraction` or web scrapers) restrict incoming text size directly at the socket level. Payloads are clipped to explicit character thresholds before they can pass to the Thalamus or Prefrontal Cortex, protecting the system's token budget.
