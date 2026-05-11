# BRAIN OS: CLAUDE HANDOFF & EXECUTION DIRECTIVES

## 1. The Core Philosophy
- **Biomimetic Architecture:** This is an agentic swarm orchestrator modeled after human neuroanatomy. Respect the terminology (Prefrontal Cortex = Routing/Swarm, Amygdala = Security/Threat Detection, Blood-Brain Barrier = Sandboxing, Microglia = Bug Fixing).
- **UNIX Philosophy:** Keep dependencies strictly minimal. Prioritize standard library (e.g., `ast`, `subprocess`) over massive third-party packages.
- **Zero Debt:** Prioritize clean, modern Python 3.12+ features (strict typing, native `asyncio`).
- **Shift-Left Security:** Security happens *before* execution. Do not rely on "try/except" for security. Rely on static analysis (AST Membrane) and deterministic allow-lists.
- **Zero Waste Token Economics:** Context limits are respected. The system uses a deterministic router to wake up the cheapest, fastest model for simple tasks, saving the heavy reasoning models for complex software architecture.

## 2. Tooling & Data Contracts
- **The XML Contract:** When modifying `System/tools.py`, all tool outputs must return structured XML (e.g., `<shell_output><stdout>...</stdout><stderr>...</stderr></shell_output>`). The agents rely on this contract to parse reality.
- **Sandboxing:** Never bypass the Blood-Brain Barrier (`validate_execution_path`). Autonomous agents are strictly confined to `Studio/`, `Personal/`, and `Professional/`.

## 3. Workflow Rules
- Before any sweeping architectural changes, run `pytest System/tests/`. We have a strict >80% coverage requirement.
- When fixing regressions or adding features, write the tests first.
