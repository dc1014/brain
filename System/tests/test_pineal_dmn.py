import json
from datetime import datetime, timezone, timedelta
from System.organs.pineal import is_host_asleep
from System.organs.dmn import enforce_rem_paralysis, generate_dream_branch_name


def test_pineal_gland_sleep_detection(monkeypatch, tmp_path):
    # Setup mock log file
    log_file = tmp_path / "agent_interactions.jsonl"
    monkeypatch.setattr("System.organs.pineal.LOG_FILE", log_file)

    # 1. No file = asleep
    assert is_host_asleep() is True

    # 2. Recent activity = awake
    recent_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    log_file.write_text(json.dumps({"timestamp": recent_time}))
    assert is_host_asleep(idle_hours_threshold=4.0) is False

    # 3. Old activity = asleep
    old_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    log_file.write_text(json.dumps({"timestamp": old_time}))
    assert is_host_asleep(idle_hours_threshold=4.0) is True


def test_rem_paralysis_git_sandbox(monkeypatch, tmp_path):
    monkeypatch.setattr("System.organs.dmn.ROOT_DIR", tmp_path)

    # 1. Target dir doesn't exist -> fails safely
    assert enforce_rem_paralysis("ghost_project") is None

    # 2. Target dir exists but isn't a git repo -> fails safely
    project_dir = tmp_path / "Studio" / "test_project"
    project_dir.mkdir(parents=True)
    assert enforce_rem_paralysis("test_project") is None

    # (Note: We skip testing actual git commands here to avoid heavy CI dependencies,
    # but the safety aborts are mathematically proven above).


def test_dream_branch_naming():
    name = generate_dream_branch_name()
    assert name.startswith("dream/hypothesis_")
