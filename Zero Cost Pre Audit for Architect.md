### The Zero-Cost Pre-Audit (How it Works)

Think of this as a Git Pre-Commit hook for your AI. Right now, our pipeline looks like this: `Architect (Drafts Code)` -> `Auditor (Evaluates Code)`

The problem is that the Auditor (Claude 3.5 Sonnet) is essentially an expensive Senior Staff Engineer. If the Architect forgets a closing parenthesis in a Python script, paying a Senior Staff Engineer to say "You missed a parenthesis" is a massive waste of resources.

Here is how we build the **Deterministic Pre-Audit**:

**1. The Trigger (Intercepting the Pipeline)** In `runtime.py`, after the `architect` finishes its turn, we look at the `step_result.actions` array. If we see `[WRITE] Studio/Project/main.py` or `[WRITE] Studio/Project/app.tsx`, we pause the pipeline.

**2. The Execution (Local Subprocess)** We use Python's built-in `subprocess` module to run a local compiler or linter against that specific file.

- For Python: We run `uv run ruff check path/to/file`
    
- For TypeScript: We run `npx tsc --noEmit` or `npx eslint`
    

**3. The Autonomous Kickback** Linters return an exit code of `0` if the code is perfect, and `1` if there is a syntax error.

- **If Exit Code 0:** The code compiles. We pass it to the Auditor for a semantic review (checking if the business logic matches the prompt).
    
- **If Exit Code 1:** We catch the `stderr` from the terminal. We **skip the Auditor entirely** and dynamically inject a new `architect` step into the front of the pipeline with a prompt like:
    
    > _"SYSTEM HALT: Your code failed to compile. The local linter threw this exact error: `[Insert Stderr here]`. Fix this syntax error and rewrite the file."_
    

### Why this is the ultimate Token Economics hack:

Running a local linter takes **0.2 seconds and costs $0.00**. By the time the Auditor actually wakes up to grade the code, you are mathematically guaranteed that the code compiles, the imports are valid, and there are no syntax errors. The Auditor can focus 100% of its tokens on evaluating the actual logic and ATDD requirements.