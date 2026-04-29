# 🧠 The Second Brain Ecosystem
An AI-driven, fully autonomous personal knowledge base and development environment.

This repository serves as the central hub for a unified "Second Brain." By leveraging the Model Context Protocol (MCP), we have bridged the gap between local file systems, coding IDEs, cloud services, and AI reasoning engines.

The AI is no longer just a chatbot; it is an active participant in this workspace that can read your schedule, push code, search the web, and document its own findings into your personal wiki.

## 🏗️ Core Architecture
This ecosystem relies on three foundational pillars:

Obsidian (The Vault): A local repository of plain-text Markdown files serving as the explicit knowledge base.

Windsurf (The IDE): The primary coding environment, featuring native AI web browsing and code generation.

Claude (The Engine): The reasoning core, connected via the Claude CLI, utilizing MCP servers as its "hands and eyes" to interact with the real world.

## 🔌 The MCP Nervous System (Capabilities)
The true power of this Second Brain comes from its tailored MCP servers. Each server grants the AI specific tools to interact with your digital life:

1. 🗄️ Obsidian (Filesystem MCP)
What it does: Grants the AI read/write access to the local Markdown vault.

How it works: Uses the official Anthropic Filesystem server, bypassing buggy community plugins. It natively parses folders, creates notes, and searches your thoughts.

Security: Hard-restricted to the C:/Users/Admin/Brain directory.

2. 🧠 Memory MCP
What it does: Cures AI amnesia by creating a persistent, local Knowledge Graph.

How it works: As you interact, the AI automatically extracts entities (people, APIs, projects) and observations (preferences, bugs, architectural decisions) and maps their relationships.

Result: You never have to re-explain your coding style or project context in a new chat.

3. 📅 Google Calendar MCP
What it does: Reads and manages your daily schedule.

How it works: Authenticated via local GCP OAuth credentials (gcp-oauth.keys.json), allowing the AI to prep you for upcoming meetings or block out coding time.

4. ☁️ Google Drive MCP
What it does: Connects your local brain to cloud documents.

How it works: Shares the same OAuth pipeline as Calendar, enabling the AI to pull context from cloud-stored PDFs, spreadsheets, and shared docs.

5. 🐙 GitHub MCP
What it does: Allows the AI to read private repositories, create PRs, and push code.

How it works: Connected directly via Claude's cloud registry (api.githubcopilot.com/mcp), bypassing local Windows browser execution bugs entirely. Authenticated via a secure Personal Access Token (PAT).

6. 🌐 Brave Search MCP
What it does: Gives the AI real-time access to the live internet.

How it works: Replaces the unstable fetch package. It uses a secure REST API to read documentation, debug stack traces, and pull current facts into your Obsidian vault.

## 🔐 Security & Credential Management
Because this brain connects to private data, security is paramount. No secrets are stored in the main configuration file.

.env File: Stores the BRAVE_API_KEY and other dynamic variables.

.claude.json: The master configuration file, which uses a secure dotenv-cli wrapper (via Windows cmd.exe) to inject secrets into the communication pipes only at runtime.

Cloud Configs: GitHub tokens are stored in Claude's secure user-level memory, completely isolated from the workspace repository.

Git/Claude Ignore: All credential files (.env, gcp-oauth.keys.json) are strictly blocked in .gitignore and .claudeignore to prevent accidental commits or AI scraping.

## 🚀 How to Use Your Second Brain
Because everything is interconnected, you can now use natural language to trigger complex, multi-platform workflows.

Example Workflows in Claude CLI or Windsurf:

"Review the React documentation via Brave Search, write a summary of the new hooks into my Obsidian vault, and create a new feature branch on GitHub with the boilerplate code."

"Look at my Google Calendar for tomorrow. Based on my meetings, draft an agenda document in Google Drive, and remind my Memory graph that I prefer morning meetings."

"Read the Authentication_API node from your Memory graph, check my Obsidian vault for the old implementation, and write the updated Python code directly to my project folder."

## 🛠️ Windows Troubleshooting & Triumphs
This specific build includes custom engineering to bypass critical Windows 11/Node.js pipe bugs common in 2026:

The cmd.exe Wrapper: Used for servers requiring environment variables (Brave Search) to prevent Windows from scrambling standard I/O pipes.

The Direct Node Path: Used for heavy-data servers (Obsidian/Filesystem). We bypassed npx entirely, pointing pure node directly at the compiled dist/index.js file to ensure flawless data streaming.