
### The Reality of OSS Test Coverage

In the Open Source world, test coverage is a heavily debated metric. Here is the candid truth: **100% global test coverage is usually a vanity metric** that leads to brittle tests (where you end up testing Python's `print()` function instead of your logic).

However, there is a widely accepted tiered standard for production-grade OSS:

- **80% - The "Responsible" Baseline:** This catches the vast majority of regressions. Most major OSS projects aim here.
    
- **90% - The "Enterprise" Standard:** Expected for core libraries (like `requests` or `FastAPI`).
    
- **100% - The "Zero-Debt Core" Standard:** You demand 100% coverage _only_ on critical bounded contexts: Security sandboxes, Context Window pruning, and Circuit Breakers.
    

For Brain OS, we don't need to test if the Typer CLI can print colored panels. But we **absolutely must have 100% coverage** on `llm.py` and `sandbox.py` because they are the physical boundary between the AI and your hard drive.

Let's build that boundary right now.
