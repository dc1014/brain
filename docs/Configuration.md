# ⚙️ Configuration & Customization Blueprint: Tuning the Cognitive Matrix

CoreTex OS isolates its cognitive behavior, model mapping, and background loops entirely from its Python execution code. The system utilizes a "Zero-Debt" architecture, separating biological hardware limits from cognitive agent identities.

By altering these files, developers can swap model endpoints, adjust sub-agent personas, customize file routing permissions, and calibrate behavioral sensitivities without touching a single line of application source code.

---

## 🎯 Summary of Configuration Profile Domains

| Configuration Profile | Target File Path | Neuroanatomical Strategy & Operational Impact |
| --- | --- | --- |
| **Personas & Logic** | `System/agents/*.md` | Dictates explicit sub-agent system instructions, intrinsic toolsets, and behavioral boundaries using a compiled Markdown/Jinja engine. |
| **Pipeline Routing** | `System/config/routes.yaml` | Connects executive routes with explicit swarm arrays and contextually grants dangerous tools (least-privilege safety). |
| **Endpoint DNA** | `System/config/system.yaml` | Maps provider identifiers, aliases, and fallbacks, updating processing pathways across the entire brain ecosystem. |
| **Vitals & Rhythms** | `System/config/system.yaml` | Calibrates daily token budgets, background process throttling windows, and calendar day sleep cycle execution clocks. |
| **Tension Management** | `System/config/system.yaml` | Calibrates error-loop limits, automatically triggering low-temperature model elevations to override stuck logic traps. |
| **Signal Translation** | `System/config/system.yaml` | Translates raw external webhook payloads into clean sentences before passing them securely up the central signal spine. |

---

## 🧭 The Configuration Landscape

```text
               [System Command / Inbound Webhook Input]
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ 1. Core Vitals & Hardware Limits (`system.yaml`) │
         └────────────────────────┬─────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ 2. Intent Pipelines & Tool Grants (`routes.yaml`)│
         └────────────────────────┬─────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ 3. Personas & Jinja Prompts (`agents/*.md`)      │
         └──────────────────────────────────────────────────┘
```

---

## 🧬 1. The Genetic Code: Personas & Prompts

### The Compiled Markdown Engine (`System/agents/*.md`)

CoreTex OS does not use monolithic YAML files for agent definitions. Instead, every agent is a standard Obsidian Markdown note. This allows for massive, readable prompts, Few-Shot examples, and dynamic context injection.

```markdown
---
name: Subconscious Daydreamer
description: Background synthesis engine that actively investigates goals.
model: openai/gpt-4o-mini
fallbacks:
  - openrouter/anthropic/claude-3-haiku
temperature: 0.6
max_tokens: 4000
creates_milestone: false
tools:
  - read_safe_file
  - search_vault
---
You are the Subconscious Daydreamer of CoreTex OS.

Your execution domain is currently: {{ domain }}
The system time is: {{ timestamp }}

PHASE 1 (INVESTIGATION): Actively use your tools to gather context on the user's Active Subgoals.
```

* **How to Modify:** Open any `.md` file in `System/agents/` and edit the text.
* **Systemic Effect:** The OS cryptographically hashes the `agents/` directory. If you hit `CTRL+S` in your editor, the OS compiler silently hot-reloads the agent into memory in microseconds without needing a reboot.
* **Best Practice:** Define *Intrinsic Tools* (tools an agent absolutely needs to function, like `search_vault` for the Daydreamer) inside the frontmatter. Leave dangerous tools (like `execute_code`) for the `routes.yaml` file to grant dynamically.

---

## 🧠 2. Synaptic Signal Routing & Execution

### Orchestrating Action Pipelines (`System/config/routes.yaml`)

The `routes.yaml` matrix acts as the brain's execution directory. It dictates the pipeline order (including parallel Swarms) and dynamically grants *Contextual Tools* to agents based purely on the route they are running on.

```yaml
# --- System/config/routes.yaml ---
routes:
  CODE_FULLSTACK:
    - agent: swarm_architect
    - swarm:
        - agent: frontend_engineer
          tools: [execute, map_spatial_dependencies]
        - agent: backend_engineer
          tools: [execute, map_spatial_dependencies]
    - agent: qa_auditor
      tools: [execute, vision]
```

* **How to Modify:** Add or remove tool blocks, sequential agents, or `swarm:` parallel arrays.
* **Systemic Effect:** Controls sub-agent permissions. The `qa_auditor` above is dynamically granted the `vision` tool to inspect the frontend UI, but only on the `CODE_FULLSTACK` route.
* **Best Practice:** Apply the principle of least privilege to file permissions. Never grant the `execute` tool in an agent's Markdown frontmatter; always grant it strictly in `routes.yaml` on trusted pipelines.

---

## 🫁 3. Homeostasis, Stress Thresholds, & Background Daemons

All core biological limits are maintained in `System/config/system.yaml`.

### Mapping Providers & Aliases

The `models` block defines the model endpoints used throughout the operating system. CoreTex natively handles fallback routing if a provider goes offline.

```yaml
# --- Inside System/config/system.yaml ---
models:
  gemini_flash: "gemini/gemini-2.5-flash"
  claude_haiku: "anthropic/claude-haiku-4-5"
  gpt_mini: "openai/gpt-4o-mini"
  default: "openai/gpt-4o-mini"
  fast: "openai/gpt-4o-mini"
```

### Pace & Rhythm Configurations (Medulla)

The `medulla` block configures the background drives managed by the master brainstem daemon.

```yaml
# --- Inside System/config/system.yaml ---
medulla:
  state_parameters:
    awake_port: 8080
    max_daily_token_budget: 500000

  circadian_rhythm:
    sleep_trigger_time: "03:00"
    daydream_duration_minutes: 45
    auto_purge_lymph_nodes: false
```

* **How to Modify:** Adjust numerical thresholds, toggle boolean daemon state flags (`true`/`false`), or append folder directories to file tracking scopes.
* **Systemic Effect:** Calibrates operational pacing, local network ports, background watch folders, and the daily token budget to prevent runaway LLM costs.

### Domain Memory Mapping

This configuration pairs system domains with persistent Markdown consolidation paths.

```yaml
# --- Inside System/config/system.yaml ---
domains:
  META: "Meta/global-memory.md"
  PERSONAL: "Personal/personal-memory.md"
  PROFESSIONAL: "Professional/professional-memory.md"
  STUDIO: "Studio/studio-memory.md"
```

### Calibrating Tension & Model Shifts (Anterior Cingulate Cortex)

The conflict monitoring blocks manage error loops and operational stress thresholds.

```yaml
# --- Inside System/config/system.yaml ---
conflict_monitoring:
  max_consecutive_tool_failures: 3
  epistemic_drift_threshold: 0.75

neuromodulation:
  high_stress:
    temperature: 0.0
    engine_override: "claude-3-5-sonnet"
  low_stress:
    temperature: 0.7
    engine_override: "local-slm"
```

* **Systemic Effect:** Alters how the system handles tool failures and errors. If consecutive tool execution errors climb past your limit, the system drops its model temperature and upgrades processing to your selected high-stress model to fix the issue deterministically.

---

## 📡 4. External Environment Webhook Translation

### Formatting Webhook Actions

The `webhooks` block configures how the HTTP network interface transforms raw inbound requests into clean text sentences.

```yaml
# --- Inside System/config/system.yaml ---
webhooks:
  github:
    route_name: "github"
    secret_env_var: "GITHUB_WEBHOOK_SECRET"
    signature_header: "X-Hub-Signature-256"
    payload_mapping:
      repo: "repository.name"
      pusher: "pusher.name"
    target_action: "exteroceptive"
    template: "Environment Shift: Repository {repo} received a push from {pusher}."
```

* **How to Modify:** Map data paths using dot notation keys matching your payload data structure, and update the string assembly `template`.
* **Systemic Effect:** Controls how background signals are packaged before traveling up the system spine.
* **Best Practice:** Keep the target environment variable indicator mapped under `secret_env_var`. This instructs the server to cryptographically verify inbound request payloads against your secret key before processing data.

---

## 🎯 Customization Guardrails & Verification Checks

Before committing configuration modifications or deploying updated YAML files to your main repository branch, execute the following local checks to ensure configuration safety and prevent boot crashes:

1. **Verify Formatting Structure:** Run the automated configuration validator to check for trailing indentation errors or unclosed text quotes:
```bash
uv run ruff check . --fix
```

2. **Execute Validation Checks:** Run the test suite to confirm model configuration names, Markdown frontmatters, and routing bounds line up correctly:
```bash
uv run pytest System/tests/
```
