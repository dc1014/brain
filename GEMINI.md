# OBSIDIAN VAULT LOCAL DIRECTIVES

## 1. Context Initialization (The "Current State" Pointer)
- Before answering any complex queries regarding my personal or professional life, use your filesystem tool to read `System/Current-Focus.md`. 
- This file contains my active projects, weekly goals, and current headspace. Align your advice and synthesis with the priorities listed there.

## 2. Vault Maintenance & Markdown Rules
- **Formatting:** All internal links must use strict Obsidian wikilink syntax: `[[Page Name]]`. Do not use standard Markdown links `[Page Name](Page-Name.md)` for internal files.
- **Frontmatter:** When creating new notes, you must include a standard YAML frontmatter block with `aliases: []`, `tags: []`, and `date: YYYY-MM-DD`.
- **Atomic Notes:** If I ask you to summarize a large meeting or architecture document, extract distinct concepts into separate, bite-sized notes and create a central Map of Content (MOC) note linking them together.

## 3. Git-Backed Awareness
- This vault is tracked via Git. If I ask you to make sweeping changes or reorganize folders via MCP, remind me to ensure I have a clean working tree or suggest I run `git commit` first so we can diff your changes.
- Treat the `/Templates` folder as read-only unless I explicitly instruct you to modify a template.