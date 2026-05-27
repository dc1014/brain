# Context Archaeology

`ctx archaeology` scans a local project, vault, or note folder for hidden leverage
patterns and writes a brief with an evidence trail and next moves.

This is a provider-free CoreTex reflex: it does not call an LLM, shell out to
`grep`, or require external services. It is meant to be the deterministic first
step before a heavier `task` or `daydream` loop.

## Usage

```bash
ctx archaeology ./path/to/vault --goal "Launch planning"
```

Optional output path:

```bash
ctx archaeology ./path/to/vault \
  --goal "Find the next commercial wedge" \
  --output Professional/context-archaeology-brief.md
```

## What it produces

- files/bytes scanned,
- strongest recurring themes,
- evidence by source file,
- a short hidden-pattern synthesis,
- concrete next moves.

## Why it exists

A lot of useful work hides between notes rather than inside any single file.
Context Archaeology gives CoreTex a native way to surface those overlaps before
asking an LLM to reason over them.
