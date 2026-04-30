# 🧠 Brain OS

Welcome to the open-core engine of Brain OS.

## 🌟 The Philosophy (Open-Core)
* The system architecture, API routers, and AI prompts are open-source. 
* Your personal data, journals, codebase, and business IP remain 100% local and secured.

## 🏗️ Architecture
This system uses a **Multi-Agent Trinity** powered by `uv` and `LiteLLM`:
1. **The Orchestrator (Gemini):** Analyzes intent, breaks down tasks, and synthesizes final outputs.
2. **The Worker (Claude):** Performs the heavy lifting, deep structured thinking, and file generation.
3. **The Auditor (ChatGPT):** Reviews code, challenges blind spots, and ensures logic holds up.

## 🚀 Quick Start Guide

### 1. Prerequisites
* Install Python 3.12+
* Install `uv` (The blazingly fast Python package manager)
* Install Git

### 2. Installation
Clone the core engine and lock in the dependencies:
```bash
git clone https://github.com/yourusername/brain.git
cd brain
uv sync