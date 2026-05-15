import io
import time
import tarfile
from rich.console import Console
from System.core.paths import ROOT_DIR

console = Console()


def flush_waste(max_log_lines: int = 0, max_bak_age_hours: int = 24) -> None:
    """
    The Lymphatic System.
    Compresses metabolic waste into tarballs to prevent bloat.
    If max_log_lines=0, it dynamically hunts, archives, and eradicates all token ledgers.
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
    cleared_images = 0
    trimmed_lines = 0
    ledger_cleared = False

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

        # --- 2. APEX FIX: Recursively Hunt, Archive & Eradicate Active Logs ---
        log_files = list(ROOT_DIR.rglob("agent_interactions.jsonl"))
        for idx, log_path in enumerate(log_files):
            if log_path.is_file():
                try:
                    lines = log_path.read_text(encoding="utf-8").splitlines()
                    if not lines:
                        continue

                    archived_data = ""
                    if max_log_lines == 0:
                        archived_data = "\n".join(lines) + "\n"
                        log_path.unlink()  # Eradicate
                        ledger_cleared = True
                        trimmed_lines += len(lines)
                    else:
                        if len(lines) > max_log_lines:
                            trimmed_count = len(lines) - max_log_lines
                            archived_data = "\n".join(lines[:trimmed_count]) + "\n"
                            log_path.write_text(
                                "\n".join(lines[-max_log_lines:]) + "\n",
                                encoding="utf-8",
                            )
                            trimmed_lines += trimmed_count

                    # Safely archive the waste before it is lost forever
                    if archived_data:
                        tarinfo = tarfile.TarInfo(
                            name=f"logs/archived_interactions_{timestamp}_{idx}.jsonl"
                        )
                        archived_bytes = archived_data.encode("utf-8")
                        tarinfo.size = len(archived_bytes)
                        tar.addfile(tarinfo, io.BytesIO(archived_bytes))
                except Exception:
                    pass

        # --- 3. APEX FIX: Recursively Hunt & Eradicate Phantom Fatigue Cache ---
        if max_log_lines == 0:
            for met_path in ROOT_DIR.rglob("metabolism.json"):
                if met_path.is_file():
                    try:
                        met_path.unlink()
                        ledger_cleared = True
                    except Exception:
                        pass

        # --- 4. Clear Visual Cortex Buffer ---
        visual_dir = ROOT_DIR / "Meta" / "Visual_Cortex"
        if visual_dir.exists():
            for f in visual_dir.glob("*.png"):
                if f.is_file():
                    try:
                        tar.add(f, arcname=f"media/{f.name}")
                        f.unlink()
                        cleared_images += 1
                    except Exception:
                        pass

        if cleared_images > 0:
            console.print(
                f"[dim blue]🌊 Flushed {cleared_images} ephemeral screenshots from Visual Cortex.[/dim blue]"
            )

    # --- Cleanup empty tarballs if nothing was added ---
    if cleared_baks == 0 and cleared_images == 0 and trimmed_lines == 0:
        tar_path.unlink()

    if ledger_cleared:
        console.print(
            "[bold blue]🌊 Flush complete: All ghost ledgers and metabolism caches eradicated. Tokens reset to 0.[/bold blue]"
        )
    else:
        console.print(
            "[dim blue]🌊 Flush complete: System tissues are clean. No waste archived.[/dim blue]"
        )


def purge_waste() -> None:
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
