# ⚡ Brain OS: Quick Execution

To run these, highlight the prompt and hit `Cmd + Shift + B`.

### 🏗️ Forge Operations
- `task "Use bootstrap_project to create a new project called 'My-App'"`
- `task "Run operate_forge on 'My-App' with instruction: '[START: Engineering] Fix the linting errors.'"`

### 🌙 Maintenance
- `sleep`
- `logs --limit 5`

### 🔍 Discovery
- `task "Search Studio for 'fastapi' and summarize the endpoints."`


### Other Stuff

uv run System/cli.py logs --limit 2

uv run pytest System/tests

uv run pre-commit run --all-files

uv run System/cli.py task

uv run System/cli.py sleep --synaptic
