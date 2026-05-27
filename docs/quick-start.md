# Show HN demo: first useful CoreTex loop

This is the launch-safe demo path for reviewers who want to understand CoreTex
without handing it a private repo first.

## Goal
Prove the basic loop in under a minute:

1. inspect local text,
2. bind it into CoreTex memory,
3. run one small launch-audit task,
4. produce a concrete artifact.

## Commands

```bash
./setup.sh --check || true
./ctx status
./ctx absorb examples/show-hn-mini-project --domain Professional --tags show-hn,demo,launch
./ctx task "Using examples/show-hn-mini-project, write a launch-readiness checklist to Professional/show-hn-demo-checklist.md. Focus on setup clarity, first-run errors, and safe public launch hygiene."
```

If you do not have an LLM provider configured yet, run the deterministic local
smoke instead:

```bash
python scripts/show_hn_demo.py
cat Professional/show-hn-demo-checklist.md
```

## Expected artifact

`Professional/show-hn-demo-checklist.md` should contain actionable launch checks
such as:

- copy/paste quickstart verification,
- non-mutating help/check commands,
- missing dependency diagnostics,
- no secret leakage in generated notes.

## Why this matters
Passing tests proves the engine is stable. This loop proves the product shape:
CoreTex turns local workspace context into a useful operational artifact.
