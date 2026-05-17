import time
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent


# --- 1. THE CORTEX (Event Router & Reflexes) ---
def process_sensory_event(source: str, event_type: str, payload: dict) -> None:
    """
    The Somatosensory Cortex.
    Routes incoming sensory data (local files, or future webhooks) to biological reflexes.
    """
    # Reflex A: Local File Modifications
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
                pass  # Outside safe zone

        # Micro-Reflex 2: AST Structural Mapping (Proprioception)
        valid_ast_exts = (".py", ".ts", ".tsx", ".js", ".jsx")
        if any(filepath.endswith(ext) for ext in valid_ast_exts):
            try:
                from System.ast_parser import extract_signatures

                stubs = extract_signatures(filepath)

                # Write to the Meta/AST directory so the PM can read it later instantly
                ast_dir = ROOT_DIR / "Meta" / "AST"
                ast_dir.mkdir(parents=True, exist_ok=True)

                # Create a safe, flat filename (e.g., Studio_main.py.md)
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

    # Future Extension: Webhooks
    elif source == "webhook":
        console.print(
            f"[dim]🌐 Somatosensory Cortex received remote webhook ({event_type}). Routing to DMN...[/dim]"
        )


# --- 2. SENSORY RECEPTORS (The Skin / Event Emitters) ---
def start_local_watcher(target_dir_name: str, poll_interval: int = 2) -> None:
    """
    A Zero-Debt, standard-library file watcher.
    Acts as the skin, polling for local physical changes.
    """
    watch_dir = ROOT_DIR / target_dir_name
    if not watch_dir.exists():
        console.print(
            f"[bold red]Cannot feel '{target_dir_name}'. Directory not found.[/bold red]"
        )
        return

    console.print(
        f"[bold magenta]🖐️  Somatosensory Cortex online. Feeling for changes in {watch_dir.name}/...[/bold magenta]"
    )
    console.print("[dim](Press Ctrl+C to disconnect sensory input)[/dim]\n")

    file_states: dict[Path, float] = {}
    valid_exts = {".py", ".ts", ".md"}
    ignore_dirs = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}

    try:
        while True:
            for filepath in watch_dir.rglob("*"):
                if filepath.is_file() and filepath.suffix in valid_exts:
                    if any(ignored in filepath.parts for ignored in ignore_dirs):
                        continue

                    mtime = filepath.stat().st_mtime
                    if filepath in file_states:
                        if mtime > file_states[filepath]:
                            # File changed! Fire the nerve impulse to the Cortex.
                            process_sensory_event(
                                "local_fs", "file_modified", {"filepath": str(filepath)}
                            )
                            file_states[filepath] = mtime
                    else:
                        # Initial state load
                        file_states[filepath] = mtime

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        console.print("\n[dim]Somatosensory Cortex offline.[/dim]")
