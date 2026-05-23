import re
import time
from System.core.paths import ROOT_DIR
from pathlib import Path
from rich.console import Console
from typing import List

console = Console()


def process_sensory_event(source: str, event_type: str, payload: dict) -> None:
    if source == "local_fs" and event_type == "file_modified":
        filepath = payload.get("filepath", "")
        file_obj = Path(filepath)

        # Micro-Reflex 1: Syntax checking on Python files
        if filepath.endswith(".py"):
            from System.tools import analyze_safe_syntax

            try:
                rel_path = str(file_obj.relative_to(ROOT_DIR))
                result = analyze_safe_syntax(rel_path)

                if "❌" in result:
                    console.print(
                        f"\n[bold red]🦟 Somatosensory Reflex: Ouch! Syntax error detected in {file_obj.name}[/bold red]"
                    )
                    console.print(f"[dim]{result.strip()}[/dim]")
                else:
                    console.print(
                        f"[dim]🦟 Reflex: {file_obj.name} saved cleanly.[/dim]"
                    )
            except ValueError:
                pass

        # Micro-Reflex 2: AST Structural Mapping (Proprioception)
        valid_ast_exts = (".py", ".ts", ".tsx", ".js", ".jsx")
        if any(filepath.endswith(ext) for ext in valid_ast_exts):
            try:
                from System.ast_parser import extract_signatures

                stubs = extract_signatures(filepath)

                ast_dir = ROOT_DIR / "Meta" / "AST"
                ast_dir.mkdir(parents=True, exist_ok=True)

                safe_name = f"{file_obj.parent.name}_{file_obj.name}.md"
                ast_file = ast_dir / safe_name

                ast_file.write_text(
                    f"--- AST SIGNATURES FOR {file_obj.name} ---\n```\n{stubs}\n```",
                    encoding="utf-8",
                )
                console.print(
                    f"[dim]🌳 Reflex: AST Map updated for {file_obj.name}[/dim]"
                )
            except Exception as e:
                console.print(f"[dim red]AST Reflex failed: {e}[/dim red]")

        # Micro-Reflex 3: Hippocampus Real-Time Encoding
        try:
            from System.neuroanatomy.limbic.hippocampus import encode_memory

            content = file_obj.read_text(encoding="utf-8")
            encode_memory(str(file_obj.relative_to(ROOT_DIR)), content)
            console.print(
                f"[dim]🧠 Reflex: Hippocampus encoded memory for {file_obj.name}[/dim]"
            )
        except Exception:
            pass

    elif source == "webhook":
        console.print(
            f"[dim]🌐 Somatosensory Cortex received remote webhook ({event_type}). Routing to DMN...[/dim]"
        )


def start_local_watcher(
    target_dirs: list[str] | None = None, poll_interval: int = 2
) -> None:
    """Watches multiple domains simultaneously for file changes."""
    if not target_dirs:
        target_dirs = ["Studio", "Meta", "Personal", "Professional"]

    watch_paths = []
    for t in target_dirs:
        p = ROOT_DIR / t
        if p.exists():
            watch_paths.append(p)

    if not watch_paths:
        console.print(
            "[bold red]Cannot feel any domains. Directories not found.[/bold red]"
        )
        return

    console.print(
        f"[bold magenta]🖐️  Somatosensory Cortex online. Feeling for changes across {len(watch_paths)} domains...[/bold magenta]"
    )
    console.print("[dim](Press Ctrl+C to disconnect sensory input)[/dim]\n")

    file_states: dict[Path, float] = {}
    valid_exts = {".py", ".ts", ".tsx", ".md", ".json", ".txt"}
    ignore_dirs = {
        ".git",
        "node_modules",
        ".venv",
        "__pycache__",
        "dist",
        "build",
        "logs",
    }

    try:
        last_sleep_check = time.time()

        while True:
            # --- CIRCADIAN RHYTHM (Check for sleep every 1 hour) ---
            current_time = time.time()
            if current_time - last_sleep_check > 3600:  # 3600 seconds = 1 hour
                from System.neuroanatomy.autonomic.pineal import (
                    is_host_asleep,
                    enter_sleep_cycle,
                )

                if is_host_asleep():
                    enter_sleep_cycle()
                last_sleep_check = current_time

            # --- SENSORY REFLEXES ---
            for watch_dir in watch_paths:
                for filepath in watch_dir.rglob("*"):
                    if filepath.is_file() and filepath.suffix in valid_exts:
                        if any(ignored in filepath.parts for ignored in ignore_dirs):
                            continue

                        mtime = filepath.stat().st_mtime
                        if filepath in file_states:
                            if mtime > file_states[filepath]:
                                process_sensory_event(
                                    "local_fs",
                                    "file_modified",
                                    {"filepath": str(filepath)},
                                )
                                file_states[filepath] = mtime
                        else:
                            file_states[filepath] = mtime

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        console.print("\n[dim]Somatosensory Cortex offline.[/dim]")


class SensoryTransducer:
    """
    A pure-Python deterministic sensory engine inspired by TokenJuice.
    Protects Prefrontal Lobe context windows from verbose terminal slop.
    """

    def __init__(self, max_lines: int = 50, head_slice: int = 20, tail_slice: int = 25):
        self.max_lines = max_lines
        self.head_slice = head_slice
        self.tail_slice = tail_slice

        # Pre-compiled fast regex engines for terminal noise removal
        self.ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.progress_pattern = re.compile(
            r"([\s\d%]+[░■▰▱▬█=>-]+\s*[\d.]+[:\d]*\s*[M|K|G]?B/s|⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏)"
        )

        # ⚡ FIXED: Added explicit tracking matching for bracketed linter summaries ([*])
        self.package_noise = re.compile(
            r"^("
            r"resolved|downloaded|installed|audited|checked|funding|fetching|extracting|"
            r"requirement\s+already\s+satisfied|"
            r"\[\d+/\d+\]\s+(resolving|fetching|linking)|"
            r"\[\s*[\d.]+(ms|s)\]\s+bun\s+|"
            r"all\s+checks\s+passed|\d+\s+files?\s+would\s+be\s+reformatted|"
            r"\[\*\]\s*\d+\s+files?\s+checked"
            r")\s*.*$",
            re.IGNORECASE,
        )

    def compact_terminal_output(self, command_array: List[str], raw_output: str) -> str:
        """
        Processes safe sandbox outputs, filtering environment noise and applying
        deterministic line constraints.
        """
        if not raw_output or not command_array:
            return raw_output

        # 🛡️ SECURITY INTERCEPT: Scrub leaked vault secrets from the output stream BEFORE line truncation splits them
        from System.neuroanatomy.systemic.immune_system import vault

        raw_output = vault.mask_secrets(raw_output)

        binary = str(command_array[0]).lower().strip()

        # 🛡️ SAFE-INVENTORY POLICY: Data-view commands must remain 100% raw
        inventory_binaries = {"cat", "type", "dir", "ls"}
        if binary in inventory_binaries:
            return raw_output

        # Pass 1: Strip ANSI color codes and structural decorations instantly
        clean_text = self.ansi_escape.sub("", raw_output)

        lines = clean_text.splitlines()
        filtered_lines = []

        # Pass 2: Clean out progress indicators, spinners, and packaging metrics
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if self.progress_pattern.search(line) or self.package_noise.match(stripped):
                continue
            filtered_lines.append(line)

        # Pass 3: Enforce strict deterministic line-slicing margins
        if len(filtered_lines) > self.max_lines:
            dropped_count = len(filtered_lines) - (self.head_slice + self.tail_slice)
            head = filtered_lines[: self.head_slice]
            tail = filtered_lines[-self.tail_slice :]

            compaction_banner = f"\n--- [SENSORY COMPACTOR: Truncated {dropped_count} lines of intermediate terminal noise] ---\n"
            return "\n".join(head) + compaction_banner + "\n".join(tail)

        return "\n".join(filtered_lines)
