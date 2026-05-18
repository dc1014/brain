# ⚡ Brain OS: Command Line Interface

Brain OS is entirely modular and can be controlled via the CLI.
Run these commands from the root directory using `uv run`.

### 🧠 Core Cognition
Execute a task through the Dispatcher and Agent Swarm.
* `uv run System/cli.py task "Your instruction here"`
* **Example:** `uv run System/cli.py task "Use bootstrap_project to create a new app called 'My-App'"`
* **Example:** `uv run System/cli.py task "Search Studio for 'fastapi' and summarize the endpoints."`

### 🖐️ Sensory Input (Somatosensory Cortex)
Start the background watcher to feel for file saves across all domains and trigger autonomous reflexes (Syntax checking, AST mapping, Hippocampus memory encoding).
* `uv run System/cli.py watch`
* *Optional:* `uv run System/cli.py watch --target Studio`

### 📚 Memory Management (Hippocampus)
Manually rebuild the ephemeral SQLite search index from your flat-file markdown notes and code.
* `uv run System/cli.py reindex`

### 🌙 Autonomic States (Pineal Gland)
Force the system into a Deep Sleep cycle (Triggers the Lymphatic flush, and then REM sleep/DMN Daydreaming).
* `uv run System/cli.py sleep`

### 👁️ Sensory Perception (Sense)
Trigger Brain OS's external receptors directly from the CLI.
* `uv run Sense/cli.py screenshot "https://google.com" "google.png"` - *Takes a headless screenshot.*
* `uv run Sense/cli.py perceive "google.png" "Describe the layout."` - *Uses the Occipital Lobe to read an image.*

### 🔍 Discovery
- `task "Search Studio for 'fastapi' and summarize the endpoints."`
- `task "Run a semantic_search in Personal for notes related to 'canine training strategies'."`

### 🌊 Garbage Collection (Lymphatic System)
Manage your hard drive space and old AI logs.
* `uv run System/cli.py flush` - *Sweeps old logs and .bak snapshots into compressed `.tar.gz` Lymph Nodes.*
* `uv run System/cli.py purge` - *Destructively and permanently deletes all archived Lymph Nodes.*

### 📊 Diagnostics (Interoception)
View the most recent AI interactions, reasoning, and token usage.
* `uv run System/cli.py logs`
* *Optional:* `uv run System/cli.py logs --limit 5`

### 🛠️ Developer Checks
Run these to ensure Zero-Debt compliance before committing code.
* `uv run pytest System/tests` - *Run the biomimetic test suite.*
* `uv run pre-commit run --all-files` - *Run Shift-Left linting and typing checks.*
