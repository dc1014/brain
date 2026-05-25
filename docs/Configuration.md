# ⚙️ Configuration & Customization Blueprint: Tuning the Cognitive Matrix

CoreTex OS isolates its cognitive behavior, model mapping, and background loops entirely from its Python execution code. Everything is controlled through declarative YAML files located within the **`System/config/`** directory.

By altering these files, developers can swap model endpoints, adjust sub-agent personas, customize file routing permissions, and calibrate behavioral sensitivities without touching a single line of application source code.

---

## 🎯 Summary of Configuration Profile Domains

| Configuration Profile | Core Target File Path | Neuroanatomical Strategy & Operational Impact |
| --- | --- | --- |
| **Personas & Code Rules** | `System/config/agents.yaml` | Dictates explicit sub-agent system instructions and behavioral boundaries using clean XML structure enforcement. |
| **Endpoint DNA** | `System/config/models.yaml` | Maps provider identifiers and aliases, updating processing pathways across the entire brain ecosystem instantly. |
| **Pipeline Routing** | `System/config/routes.yaml` | Connects executive routes with explicit tool combinations and relative folder context boundaries (least-privilege safety). |
| **Vitals & Rhythms** | `System/config/medulla.yaml` | Calibrates daily token budgets, background process throttling windows, and calendar day sleep cycle execution clocks. |
| **Tension Management** | `System/config/acc.yaml` | Calibrates error-loop limits, automatically triggering low-temperature model elevations to override stuck logic traps. |
| **Signal Translation** | `System/config/webhooks.yaml` | Translates raw payload data maps into clean sentences before passing them securely up the central signal spine. |

---

## 🧭 The Configuration Landscape

```text
               [System Command / Inbound Webhook Input]
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ 1. Core Vitals & Sleep Schedules (`medulla.yaml`)│
         └────────────────────────┬─────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ 2. Intent Pipelines & Folder Scopes (`routes.yaml`)│
         └────────────────────────┬─────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ 3. Persona Prompts & Protocols (`agents.yaml`)   │
         └────────────────────────┬─────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ 4. Model Endpoints & Provider Keys (`models.yaml`)│
         └────────────────────────┬─────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────────────────────┐
         │ 5. Stress Tolerances & Backoffs (`acc.yaml`)     │
         └──────────────────────────────────────────────────┘

```

---

## 🧬 1. The Genetic Code: Models & Personas

### Mapping Providers & Aliases (`System/config/models.yaml`)

The `models.yaml` configuration defines the model endpoints used throughout the operating system. CoreTex OS uses LiteLLM under the hood, natively supporting over 100 commercial cloud and local model providers (including OpenAI, Anthropic, Google Gemini, OpenRouter, and local Ollama frameworks).

```yaml
# --- System/config/models.yaml ---
models:
  gemini_flash: "gemini/gemini-2.5-flash"
  claude_haiku: "anthropic/claude-haiku-4-5"
  gpt_mini: "openai/gpt-4o-mini"
  claude_sonnet: "anthropic/claude-sonnet-4-5"
  local_slm: "ollama/llama3"
  default: "openai/gpt-4o-mini"

```

* **How to Modify:** Change the right-hand string to match your provider's model signature (e.g., `"openai/gpt-4o"` or `"ollama/mistral"`).
* **Systemic Effect:** Modifies model assignments across the brain. Updating an alias string instantly updates every sub-agent assigned to that keyword profile.
* **Best Practice:** Keep the single `default` key pointing to a cheap model setup. If you operate using exactly one provider API key, map your chosen target identifier to the `default` placeholder to activate auto-discovery fallbacks.

### Modifying Operational Personas (`System/config/agents.yaml`)

Sub-agent roles and behavioral guidelines are managed inside `agents.yaml`. Commands pass through these specific blocks to guide text generation.

```yaml
# --- System/config/agents.yaml ---
agents:
  dispatcher:
    name: "Thalamus (Dispatcher)"
    model: "gemini_flash"
    system_prompt: |
      <system_instructions>
      <persona>
      You are the CoreTex OS Thalamus. Your ONLY job is to validate and route user tasks.
      </persona>
      <execution_protocol>
      <step number="1">Evaluate systemic capabilities...</step>
      </execution_protocol>
      </system_instructions>

```

* **How to Modify:** Rewrite the plaintext `system_prompt` field. You can reference any model alias mapped within `models.yaml` inside the agent's `model` key.
* **Systemic Effect:** Modifies sub-agent actions, error analysis parameters, and tool call generation tempos.
* **Best Practice:** Enforce strict XML block layouts inside system prompts. Use `<system_instructions>`, `<persona>`, and ordered `<step>` milestones. This structural separation helps models track workflow criteria and ensures Broca's Area can auto-heal incomplete text blocks if generation hits a token limit.

---

## 🧠 2. Synaptic Signal Routing & Folder Scopes

### Orchestrating Action Pipelines (`System/config/routes.yaml`)

The `routes.yaml` matrix acts as the brain's routing directory. When the dispatcher determines a task route, this config specifies which agents are deployed, what toolsets are exposed, and which directory partitions are accessible.

```yaml
# --- System/config/routes.yaml ---
routes:
  WORKSPACE:
    - agent: "archivist"
      tools: ["base", "write", "sense_environment"]
      context: ["Meta", "Domain"]
  SWARM:
    - agent: "swarm_architect"
      tools: ["base", "write", "sense_environment"]
      context: ["Meta", "Domain", "Studio", "Professional"]
    - swarm:
        - agent: "frontend_engineer"
          tools: ["base", "write", "execute", "map_spatial_dependencies"]
          context: ["Studio"]

```

* **How to Modify:** Add or remove tool blocks or folder tags within an explicit route category.
* **Systemic Effect:** Controls sub-agent permissions. If an engineer sub-agent requests execution permissions outside its configured `context` directory array, the tool wrapper drops the action before disk access can occur.
* **Best Practice:** Apply the principle of least privilege to file permissions. Restrict heavy, autonomous code writing paths (`execute`) to isolated workspace folders like `Studio`, while locking personal long-term memory tracks to safe zones like `Personal`.

### Domain Memory Mapping (`System/config/memory.yaml`)

This configuration pairs system domains with persistent Markdown consolidation paths.

```yaml
# --- System/config/memory.yaml ---
domains:
  META: "Meta/global-memory.md"
  PERSONAL: "Personal/personal-memory.md"
  PROFESSIONAL: "Professional/professional-memory.md"
  STUDIO: "Studio/studio-memory.md"

```

* **How to Modify:** Update path strings to point to alternative targets within your repository.
* **Systemic Effect:** Changes where long-term documentation is written. During sleep cycles, summarized short-term tracks append to these destination files.

---

## 🫁 3. Homeostasis, Stress Thresholds, & Background Daemons

### Pace & Rhythm Configurations (`System/config/medulla.yaml`)

The `medulla.yaml` file configures the background drives managed by the master brainstem daemon.

```yaml
# --- System/config/medulla.yaml ---
medulla:
  state_parameters:
    awake_port: 8080
    max_daily_token_budget: 500000

  circadian_rhythm:
    sleep_trigger_time: "03:00"
    daydream_duration_minutes: 45
    auto_purge_lymph_nodes: false

  background_daemons:
    file_watcher:
      enabled: true
      polling_throttle_ms: 1000
      targets: ["Personal", "Professional", "Studio"]

```

* **How to Modify:** Adjust numerical thresholds, toggle boolean daemon state flags (`true`/`false`), or append folder directories to file tracking scopes.
* **Systemic Effect:** Calibrates operational pacing, local network ports, background watch folders, and the daily token budget.
* **Best Practice:** Keep `auto_purge_lymph_nodes` set to `false`. This instructs the system to archive historical logs into compressed folders during maintenance rather than deleting data completely, giving you a chance to manually inspect file rollbacks.

### Calibrating Tension & Model Shifts (`System/config/acc.yaml`)

The Anterior Cingulate Cortex file `acc.yaml` monitors logic loops and manages operational stress thresholds.

```yaml
# --- System/config/acc.yaml ---
conflict_monitoring:
  max_consecutive_tool_failures: 3
  epistemic_drift_threshold: 0.75
  sunk_cost_line_limit: 3

neuromodulation:
  high_stress:
    temperature: 0.0
    engine_override: "claude-3-5-sonnet"
  low_stress:
    temperature: 0.7
    engine_override: "local-slm"

```

* **How to Modify:** Adjust tool failure counts, shift drift thresholds, or modify model overrides for high-stress states.
* **Systemic Effect:** Alters how the system handles tool failures and errors. If consecutive tool execution errors climb past your limit, the system drops its model temperature and upgrades processing to your selected high-stress model to fix the issue.
* **Best Practice:** Set the `high_stress.temperature` value to exactly `0.0`. This removes random output variation, forcing deterministic code analysis and tool call tracking when debugging system failures.

---

## 📡 4. External Environment Webhook Translation

### Formatting Webhook Actions (`System/config/webhooks.yaml`)

The `webhooks.yaml` file configures how the HTTP network interface transforms raw inbound requests into clean text sentences.

```yaml
# --- System/config/webhooks.yaml ---
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
uv run pre-commit run --all-files

```


2. **Execute Validation Checks:** Run the test suite to confirm model configuration names and routing bounds line up correctly with target modules:
```bash
uv run pytest System/tests/

```
