# --- System/tests/autonomic/test_vestibular.py ---
import json
import pytest
import shutil
from System.neuroanatomy.autonomic.vestibular import (
    create_snapshot,
    commit_transaction,
    restore_balance,
)
import System.neuroanatomy.autonomic.vestibular as vestibular_mod


@pytest.fixture(autouse=True)
def clean_vestibular_workspace(tmp_path, monkeypatch):
    """Isolates the snapshot and ledger paths cleanly to temporary testing directories."""
    monkeypatch.setattr(vestibular_mod, "SNAPSHOT_DIR", tmp_path / "snapshots")
    monkeypatch.setattr(
        vestibular_mod, "LEDGER_FILE", tmp_path / "snapshot_ledger.json"
    )
    yield
    # Clean up leftovers
    if (tmp_path / "snapshots").exists():
        shutil.rmtree(tmp_path / "snapshots", ignore_errors=True)
    if (tmp_path / "snapshot_ledger.json").exists():
        (tmp_path / "snapshot_ledger.json").unlink(missing_ok=True)


def test_create_snapshot_success(tmp_path):
    """Proves that a workspace directory snapshot can be captured and logged atomically."""
    # Setup dummy workspace target source
    source_dir = tmp_path / "Studio" / "MyProject"
    source_dir.mkdir(parents=True)
    (source_dir / "index.html").write_text("<h1>Hello</h1>", encoding="utf-8")

    # Run functional snapshotting routine
    create_snapshot(source_dir)

    # Assert snapshot exists in backup storage directory
    snap_backup = vestibular_mod.SNAPSHOT_DIR / "MyProject"
    assert snap_backup.exists()
    assert (snap_backup / "index.html").exists()

    # Assert ledger tracked the mapping
    with open(vestibular_mod.LEDGER_FILE, "r", encoding="utf-8") as f:
        ledger_data = json.load(f)
    assert str(source_dir) in ledger_data


def test_commit_transaction_purges_cache(tmp_path):
    """Proves that committing a transaction safely destroys temporary snapshot files."""
    vestibular_mod.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    vestibular_mod.LEDGER_FILE.touch()

    commit_transaction()

    assert not vestibular_mod.SNAPSHOT_DIR.exists()
    assert not vestibular_mod.LEDGER_FILE.exists()


def test_restore_balance_rollback_workflow(tmp_path):
    """Proves that a rollback operation completely restores previous working tree states."""
    source_dir = tmp_path / "Studio" / "MyProject"
    source_dir.mkdir(parents=True)
    (source_dir / "code.py").write_text("valid_code = True", encoding="utf-8")

    # Take pristine state snapshot
    create_snapshot(source_dir)

    # Simulate an external tool run corrupting or mutating the files
    (source_dir / "code.py").write_text("corrupted_syntax = @#$!", encoding="utf-8")
    (source_dir / "rogue.txt").touch()

    # Trigger rollback equilibrium response
    restore_balance()

    # Assert directory rolled back fully to pristine parameters
    assert (source_dir / "code.py").read_text(encoding="utf-8") == "valid_code = True"
    assert not (source_dir / "rogue.txt").exists()

    # Assert snapshots are cleared post-rollback
    assert not vestibular_mod.SNAPSHOT_DIR.exists()
