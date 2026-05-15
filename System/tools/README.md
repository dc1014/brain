# 🦾 The Peripheral Nervous System (Tools)

This directory contains the tools (motor functions) that Brain OS agents can execute.
In biological terms, if the agents are the Brain, these files are the hands, mouth, and eyes of the operating system.

## 🧬 Our 5 Core Principles
Before you contribute a new tool, you MUST adhere to the genetic code of Brain OS:

1. **Safety and Ethics First:** Tools that interact with the physical world (Webcams, Microphones, Shell Execution) MUST have a Human-in-the-Loop (HITL) prompt. The AI cannot be allowed to secretly act on the user's behalf.
2. **Unix Philosophy:** A tool should do exactly ONE thing, and do it perfectly. Do not build massive, monolithic tools. Build small reflexes and compose them.
3. **Shift Left:** Security checks must happen at the absolute boundary. Path traversals, toxic inputs, and permissions must be validated *before* the core logic ever executes.
4. **Zero Debt:** Every tool must have 100% test coverage. If your tool touches physical hardware or third-party APIs, you MUST mock it in the `System/tests` directory.
5. **Biological Inspiration:** We use biomimicry to organize the codebase. Name your functions and structure your logic based on biological equivalents whenever possible to maintain the Domain-Driven Design (DDD).

---

## 🛠️ How to Add a New Tool (OSS Contributor Guide)

Adding a new capability to Brain OS takes exactly 3 steps:

### 1. Write the Tool Wrapper
Find the appropriate file in this folder (e.g., `file_system.py` or `sensory.py`). Write your function wrapper here.
* **Security Rule:** If your tool reads or writes to the file system, you MUST import and use `is_safe_path` from `sandbox.py` to enforce the Blood-Brain Barrier!

### 2. Hook it to the Nervous System
Open `System/tools/__init__.py` and explicitly import your new function so the Motor Cortex can see it. Do not use wildcards (`*`).

    from .sensory import my_new_awesome_tool

### 3. Teach the Brain
Open `System/config/tools.yaml` and add the JSON schema for your tool. The `description` you write here is exactly how the LLM will know when and how to use your tool!
