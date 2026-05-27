#!/usr/bin/env python3
"""Deterministic Show HN demo artifact generator.

This does not call an LLM. It gives reviewers a reliable fallback that exercises
CoreTex's local-file value proposition and produces the same artifact path used
by the README-backed demo.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "show-hn-mini-project"
OUT = ROOT / "Professional" / "show-hn-demo-checklist.md"


def main() -> int:
    readme = (FIXTURE / "README.md").read_text(encoding="utf-8")
    log = (FIXTURE / "error.log").read_text(encoding="utf-8")
    findings: list[str] = []
    if "Permission denied" in log:
        findings.append("Verify launch scripts are executable in a fresh clone.")
    if "deno not found" in log.lower():
        findings.append(
            "Run setup diagnostics before sandbox-backed tasks and explain missing Deno clearly."
        )
    if "copy/pasteable" in readme:
        findings.append(
            "Keep the README quickstart copy/pasteable and non-mutating until setup is explicit."
        )
    findings.append(
        "Confirm generated launch notes avoid secrets and machine-specific absolute paths."
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "# CoreTex Show HN demo checklist\n\n"
        "Generated from `examples/show-hn-mini-project`.\n\n"
        + "\n".join(f"- {item}" for item in findings)
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
