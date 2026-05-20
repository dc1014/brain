# System/tools/ingestion.py
import re
import os
import json
from pathlib import Path
from typing import List, Tuple


class KnowledgeIngestor:
    def __init__(self, target_domain: str, default_tags: List[str]):
        from System.core.paths import ROOT_DIR

        self.root_dir = ROOT_DIR
        self.domain_dir = ROOT_DIR / target_domain
        self.default_tags = default_tags
        self.ignore_patterns = [
            r"\.git",
            r"node_modules",
            r"\.venv",
            r"__pycache__",
            r"\.DS_Store",
            r"\.obsidian",
            r"build",
            r"dist",
        ]

    def should_ignore(self, path: Path) -> bool:
        path_str = path.as_posix()
        return any(re.search(pattern, path_str) for pattern in self.ignore_patterns)

    def format_to_hybrid_contract(
        self, file_path: Path, relative_origin: Path, content: str
    ) -> str:
        """
        Safely serializes raw data text arrays while preventing rendering collapses
        by generating variable length outer code enclosures matching context density.
        """
        tags_md = " ".join([f"#{t}" for t in self.default_tags])
        clean_rel_path = file_path.relative_to(relative_origin).as_posix()
        extension = file_path.suffix.lstrip(".") or "text"

        # Calculate maximum consecutive backticks inside raw content body to ensure safe nesting
        fence = "```"
        if "```" in content:
            backtick_groups = re.findall(r"`+", content)
            max_backticks = (
                max([len(b) for b in backtick_groups]) if backtick_groups else 0
            )
            fence = "`" * (max_backticks + 1)

        return f"""# 🧠 Ingested Node: {file_path.name}
* **Source Path:** `{clean_rel_path}`
* **Tags:** {tags_md} #ingested-knowledge

<ingested_source path="{clean_rel_path}">
{fence}{extension}
{content}
{fence}
</ingested_source>
"""

    def ingest(self, source_path: Path) -> Tuple[int, int]:
        self.domain_dir.mkdir(parents=True, exist_ok=True)
        notes_count = 0
        total_bytes = 0

        if source_path.is_file():
            if self.should_ignore(source_path):
                return 0, 0
            return self._process_file(source_path, source_path.parent)

        for root, dirs, files in os.walk(source_path):
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            for file in files:
                current_file = Path(root) / file
                if self.should_ignore(current_file):
                    continue
                count, size = self._process_file(current_file, source_path)
                notes_count += count
                total_bytes += size

        return notes_count, total_bytes

    def _process_file(self, file_path: Path, relative_origin: Path) -> Tuple[int, int]:
        try:
            if file_path.suffix.lower() in [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".pdf",
                ".zip",
                ".tar",
                ".gz",
                ".exe",
            ]:
                return 0, 0

            raw_content = file_path.read_text(encoding="utf-8", errors="replace")
            if not raw_content.strip():
                return 0, 0

            formatted_md = self.format_to_hybrid_contract(
                file_path, relative_origin, raw_content
            )
            safe_name = re.sub(r"[\\/*?:\"<>|]", "_", file_path.name)
            destination_note = self.domain_dir / f"Ingested_{safe_name}.md"

            # Atomic transaction fallback verification layer
            tmp_dest = destination_note.with_suffix(".tmp")
            tmp_dest.write_text(formatted_md, encoding="utf-8")
            tmp_dest.replace(destination_note)

            self._log_to_hippocampus_stream(file_path, raw_content)
            return 1, len(raw_content.encode("utf-8"))
        except Exception:
            return 0, 0

    def _log_to_hippocampus_stream(self, file_path: Path, content: str) -> None:
        log_file = self.root_dir / "System" / "logs" / "agent_interactions.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        snippet = content[:800] + ("..." if len(content) > 800 else "")
        entry = {
            "event": "knowledge_absorption",
            "file": file_path.name,
            "snippet": snippet,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
