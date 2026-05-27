"""Local context archaeology for messy project/vault folders.

This module is intentionally deterministic and provider-free. It gives CoreTex a
native command that can inspect scattered notes, find recurring leverage themes,
and write a concrete next-move brief without shelling out to grep/cat/sed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {".md", ".txt", ".rst", ".log"}
IGNORE_PARTS = {".git", ".venv", "node_modules", "__pycache__", ".obsidian"}

THEME_LEXICON: dict[str, set[str]] = {
    "launch": {"launch", "show hn", "public", "demo", "reviewer", "audience"},
    "trust": {"setup", "diagnostic", "quiet", "safe", "risk", "leak", "sandbox"},
    "follow_through": {"follow-up", "action", "owner", "decision", "client", "meeting"},
    "artifact": {"artifact", "brief", "summary", "checklist", "note", "playbook"},
    "leverage": {"leverage", "opportunity", "wedge", "arena", "reusable", "repeatable"},
}


@dataclass(frozen=True)
class EvidenceHit:
    path: str
    terms: tuple[str, ...]


@dataclass(frozen=True)
class ArchaeologyReport:
    source: Path
    files_scanned: int
    bytes_scanned: int
    top_themes: list[tuple[str, int]]
    evidence: dict[str, list[EvidenceHit]]
    synthesis: str
    next_moves: list[str]

    def to_markdown(self) -> str:
        evidence_lines: list[str] = []
        for theme, _score in self.top_themes:
            hits = self.evidence.get(theme, [])
            if not hits:
                continue
            rendered = "; ".join(
                f"`{hit.path}` ({', '.join(hit.terms)})" for hit in hits[:4]
            )
            evidence_lines.append(f"- **{theme.replace('_', ' ')}**: {rendered}")

        return (
            "# CoreTex Context Archaeology Brief\n\n"
            f"Source: `{self.source}`\n\n"
            f"Scanned {self.files_scanned} files / {self.bytes_scanned} bytes.\n\n"
            "## Hidden pattern\n\n"
            f"{self.synthesis}\n\n"
            "## Strongest signals\n\n"
            + "\n".join(
                f"- **{theme.replace('_', ' ')}** — score {score}"
                for theme, score in self.top_themes
            )
            + "\n\n## Evidence trail\n\n"
            + "\n".join(evidence_lines)
            + "\n\n## Next moves\n\n"
            + "\n".join(f"- {move}" for move in self.next_moves)
            + "\n"
        )


def iter_text_files(source: Path) -> Iterable[Path]:
    if source.is_file():
        if source.suffix.lower() in TEXT_SUFFIXES:
            yield source
        return

    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORE_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def _relative(path: Path, source: Path) -> str:
    base = source if source.is_dir() else source.parent
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def analyze_context(source: Path, goal: str | None = None) -> ArchaeologyReport:
    source = source.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)

    scores: Counter[str] = Counter()
    evidence: dict[str, list[EvidenceHit]] = defaultdict(list)
    files_scanned = 0
    bytes_scanned = 0

    for path in iter_text_files(source):
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            continue
        files_scanned += 1
        bytes_scanned += len(text.encode("utf-8"))
        normalized = text.lower()
        for theme, terms in THEME_LEXICON.items():
            hits = tuple(sorted(term for term in terms if term in normalized))
            if hits:
                scores[theme] += len(hits)
                evidence[theme].append(EvidenceHit(_relative(path, source), hits))

    top_themes = scores.most_common(5)
    if not top_themes:
        synthesis = "No strong recurring pattern surfaced from the scanned text yet."
        next_moves = [
            "Add more notes or broaden the source folder, then rerun archaeology."
        ]
    else:
        labels = [theme.replace("_", " ") for theme, _score in top_themes[:3]]
        goal_clause = f" for `{goal}`" if goal else ""
        synthesis = (
            f"The strongest hidden pattern{goal_clause} is the overlap between "
            f"{', '.join(labels)}. CoreTex should turn that overlap into a concrete "
            "artifact instead of stopping at summary."
        )
        next_moves = _recommend_moves([theme for theme, _score in top_themes], goal)

    return ArchaeologyReport(
        source=source,
        files_scanned=files_scanned,
        bytes_scanned=bytes_scanned,
        top_themes=top_themes,
        evidence=dict(evidence),
        synthesis=synthesis,
        next_moves=next_moves,
    )


def _recommend_moves(themes: list[str], goal: str | None) -> list[str]:
    moves: list[str] = []
    if "follow_through" in themes and "artifact" in themes:
        moves.append("Produce the owner/action/decision brief hiding in the notes.")
    if "launch" in themes and "trust" in themes:
        moves.append(
            "Lead with trust-before-magic: show the evidence trail before the synthesis."
        )
    if "leverage" in themes:
        moves.append("Name the repeatable wedge and turn it into the next build bet.")
    if goal:
        moves.append(f"Package the result as a directly usable artifact for: {goal}.")
    moves.append(
        "Rerun after new notes land; this should become a living context radar."
    )
    return moves


def write_report(report: ArchaeologyReport, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_markdown(), encoding="utf-8")
    return output
