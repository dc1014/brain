import time
import tarfile
from pathlib import Path
from rich.console import Console

console = Console()
ROOT_DIR = Path(__file__).parent.parent.parent


def flush_waste(max_log_lines: int = 2000, max_bak_age_hours: int = 24) -> None:
    """
    The Lymphatic System.
    Compresses metabolic waste (old logs, orphaned snapshots) into tarballs (Lymph Nodes)
    to prevent hard drive bloat without permanently destroying user data.
    """
    console.print(
        "[dim blue]🌊 Lymphatic System: Sweeping metabolic waste to Lymph Nodes...[/dim blue]"
    )

    lymph_dir = ROOT_DIR / "Meta" / "Lymph_Nodes"
    lymph_dir.mkdir(parents=True, exist_ok=True)

    now = time.time()
    timestamp = int(now)
    tar_path = lymph_dir / f"waste_flush_{timestamp}.tar.gz"

    cleared_baks = 0
    trimmed_lines = 0

    # Use native gzip tarball compression
    with tarfile.open(tar_path, "w:gz") as tar:
        # --- 1. Archive old Vestibular snapshots ---
        vestibular_dir = ROOT_DIR / "Meta" / "Vestibular"
        if vestibular_dir.exists():
            max_age_seconds = max_bak_age_hours * 3600
            for f in vestibular_dir.glob("*.bak"):
                if f.is_file() and (now - f.stat().st_mtime > max_age_seconds):
                    try:
                        tar.add(f, arcname=f"vestibular_snapshots/{f.name}")
                        f.unlink()
                        cleared_baks += 1
                    except Exception:
                        pass

        # --- 2. Archive Old Interaction Logs ---
        log_file_path = ROOT_DIR / "logs" / "agent_interactions.jsonl"
        if log_file_path.exists():
            try:
                with open(log_file_path, "r", encoding="utf-8") as f_in:
                    lines = f_in.readlines()

                if len(lines) > max_log_lines:
                    trimmed_lines = len(lines) - max_log_lines
                    archived_lines = lines[:trimmed_lines]
                    retained_lines = lines[-max_log_lines:]

                    # Write trimmed lines to a temp file, add to tarball, then delete temp
                    temp_log = lymph_dir / f"archived_logs_{timestamp}.jsonl"
                    temp_log.write_text("".join(archived_lines), encoding="utf-8")
                    tar.add(
                        temp_log,
                        arcname=f"logs/archived_interactions_{timestamp}.jsonl",
                    )
                    temp_log.unlink()

                    # Overwrite active log with only the tail
                    with open(log_file_path, "w", encoding="utf-8") as f_out:
                        f_out.writelines(retained_lines)
            except Exception as e:
                console.print(f"[dim red]Lymphatic error archiving logs: {e}[/dim red]")

        # --- 3. Clear Visual Cortex Buffer ---
        visual_dir = ROOT_DIR / "Meta" / "Visual_Cortex"
        cleared_images = 0
        if visual_dir.exists():
            for f in visual_dir.glob("*.png"):
                if f.is_file():
                    try:
                        f.unlink()  # Permanently delete ephemeral test screenshots
                        cleared_images += 1
                    except Exception:
                        pass
        if cleared_images > 0:
            console.print(
                f"[dim blue]🌊 Flushed {cleared_images} ephemeral screenshots from Visual Cortex.[/dim blue]"
            )

    # --- Cleanup empty tarballs if nothing was added ---
    if cleared_baks == 0 and trimmed_lines == 0:
        tar_path.unlink()
        console.print(
            "[dim blue]🌊 Flush complete: System tissues are clean. No waste archived.[/dim blue]"
        )
    else:
        console.print(
            f"[bold blue]🌊 Flush complete: Archived {cleared_baks} snapshots and {trimmed_lines} log entries to Meta/Lymph_Nodes/{tar_path.name}.[/bold blue]"
        )


def purge_waste() -> None:
    """Explicit DevEx command: Permanently deletes the archived tarballs in the Lymph Nodes."""
    lymph_dir = ROOT_DIR / "Meta" / "Lymph_Nodes"
    if not lymph_dir.exists():
        console.print("[dim blue]Lymph Nodes are empty. Nothing to purge.[/dim blue]")
        return

    purged = 0
    for f in lymph_dir.glob("*.tar.gz"):
        try:
            f.unlink()
            purged += 1
        except Exception:
            pass

    console.print(
        f"[bold red]🔥 Permanently purged {purged} waste archives from Lymph Nodes.[/bold red]"
    )
