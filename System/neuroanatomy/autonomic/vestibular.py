import os
import shutil
import json
from typing import Set, Dict
from pathlib import Path
from rich.console import Console
from System.core.paths import ROOT_DIR
from System.core.locks import BiologicalLock

console = Console()
VESTIBULAR_STATE_FILE = ROOT_DIR / "Meta" / "vestibular_state.json"
BACKUP_DIR = ROOT_DIR / "Meta" / "vestibular_backups"


class VestibularSystem:
    """
    Sense of Balance & Homeostasis (Rollback).
    Takes structural snapshots of the workspace before execution and cleanly
    reverses file modifications AND orphaned directory trees upon task abortion.
    """

    def __init__(self) -> None:
        VESTIBULAR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # ⚡ ZERO-DEBT: Ignore critical OS directories
        self.protected_dirs = {
            ROOT_DIR / ".git",
            ROOT_DIR / "System",
            ROOT_DIR / "Meta",
            ROOT_DIR / ".venv",
        }
        # ⚡ ZERO-DEBT: Ignore critical root-level OS files (T-Cell Self-Recognition)
        self.protected_files = {
            "brain.bat",
            ".env",
            ".gitignore",
            "pytest.ini",
            "pyproject.toml",
            "uv.lock",
        }

    def _get_workspace_snapshot(self) -> tuple[Dict[str, float], Set[str]]:
        """Maps the exact state of files and all directories."""
        files_state: Dict[str, float] = {}
        dirs_state: Set[str] = set()

        for root, dirs, files in os.walk(ROOT_DIR):
            root_path = Path(root)

            # Skip protected directories
            if any(
                protected in root_path.parents or protected == root_path
                for protected in self.protected_dirs
            ):
                continue

            dirs_state.add(str(root_path))

            for file in files:
                if file in self.protected_files:
                    continue

                file_path = root_path / file
                try:
                    files_state[str(file_path)] = os.path.getmtime(file_path)
                except OSError:
                    pass

        return files_state, dirs_state

    def commit_transaction(self) -> None:
        """Saves a stable snapshot of the workspace structure."""
        files_state, dirs_state = self._get_workspace_snapshot()
        state = {"files": files_state, "dirs": list(dirs_state)}

        with BiologicalLock(str(VESTIBULAR_STATE_FILE)):
            with open(VESTIBULAR_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f)

        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR, ignore_errors=True)

    def snapshot_file(self, filepath: str) -> None:
        """Saves a targeted backup of a specific file before it is mutated."""
        try:
            target = (ROOT_DIR / filepath).resolve()
            if target.exists() and target.is_file():
                BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                safe_name = str(target.relative_to(ROOT_DIR)).replace(os.sep, "___")
                shutil.copy2(target, BACKUP_DIR / safe_name)
        except Exception:
            pass

    def restore_balance(self) -> None:
        """
        Rolls back the workspace.
        1. Restores modified tracked files via git checkout.
        2. Restores targeted untracked file backups.
        3. ⚡ SHIFT-LEFT: Surgically obliterates orphaned files and directory trees.
        """
        if not VESTIBULAR_STATE_FILE.exists():
            return

        try:
            with BiologicalLock(str(VESTIBULAR_STATE_FILE)):
                with open(VESTIBULAR_STATE_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)

            baseline_files: Dict[str, float] = state.get("files", {})
            baseline_dirs: Set[str] = set(state.get("dirs", []))

            console.print(
                "[dim yellow]⚖️ Vestibular System: Restoring file modifications...[/dim yellow]"
            )

            # ⚡ THE FIX: Safe subprocess checkout is encapsulated securely inside runtime operations
            import subprocess

            subprocess.run(
                ["git", "checkout", "--", "."], cwd=ROOT_DIR, capture_output=True
            )

            # 2. Restore targeted untracked file backups
            if BACKUP_DIR.exists():
                for backup_file in BACKUP_DIR.glob("*"):
                    try:
                        rel_path = backup_file.name.replace("___", os.sep)
                        target = ROOT_DIR / rel_path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_file, target)
                    except Exception:
                        pass
                shutil.rmtree(BACKUP_DIR, ignore_errors=True)

            # 3. Deep File & Directory Pruning
            current_files, current_dirs = self._get_workspace_snapshot()

            orphaned_files = set(current_files.keys()) - set(baseline_files.keys())
            pruned_file_count = 0
            for file_path_str in orphaned_files:
                try:
                    os.remove(file_path_str)
                    pruned_file_count += 1
                except OSError:
                    pass

            orphaned_dirs = current_dirs - baseline_dirs
            orphaned_dirs_sorted = sorted(list(orphaned_dirs), key=len, reverse=True)

            pruned_dir_count = 0
            for dir_path_str in orphaned_dirs_sorted:
                dir_path = Path(dir_path_str)
                if dir_path.exists() and dir_path.is_dir():
                    try:
                        shutil.rmtree(dir_path)
                        pruned_dir_count += 1
                    except OSError:
                        pass

            if pruned_file_count > 0 or pruned_dir_count > 0:
                console.print(
                    f"[dim yellow]⚖️ Vestibular System: Obliterated {pruned_file_count} orphaned files and {pruned_dir_count} directory trees.[/dim yellow]"
                )

        except Exception as e:
            console.print(
                f"[bold red]❌ Vestibular Rollback Error: {str(e)}[/bold red]"
            )


# --- Global Synaptic Hooks ---
def commit_transaction() -> None:
    VestibularSystem().commit_transaction()


def restore_balance() -> None:
    VestibularSystem().restore_balance()


def create_snapshot(filepath: str) -> None:
    VestibularSystem().snapshot_file(filepath)
