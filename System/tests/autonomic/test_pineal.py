import json
from datetime import datetime, timezone, timedelta
from System.neuroanatomy.autonomic.pineal import is_host_asleep


def test_pineal_gland_sleep_detection(monkeypatch, tmp_path):
    # Setup mock log file
    log_file = tmp_path / "agent_interactions.jsonl"
    monkeypatch.setattr("System.neuroanatomy.autonomic.pineal.LOG_FILE", log_file)

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


def test_pineal_is_host_asleep_origin_filter(tmp_path, monkeypatch):
    """Zero-Debt Test: Proves the Pineal Gland ignores AUTONOMIC background events when calculating idle sleep thresholds."""
    from System.neuroanatomy.autonomic.pineal import is_host_asleep
    from datetime import datetime, timezone, timedelta
    import json

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "agent_interactions.jsonl"

    # 1. Create a HUMAN log from 5 hours ago
    five_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    human_log = {"origin": "HUMAN", "timestamp": five_hours_ago}

    # 2. Create an AUTONOMIC log from 1 minute ago (e.g. an automated background queue task)
    one_minute_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    autonomic_log = {"origin": "AUTONOMIC", "timestamp": one_minute_ago}

    # Write both logs to the file
    log_file.write_text(
        json.dumps(human_log) + "\n" + json.dumps(autonomic_log) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("System.neuroanatomy.autonomic.pineal.LOG_FILE", log_file)

    # 3. Validation: Even though activity happened 1 minute ago, it was AUTONOMIC.
    # The human has been idle for 5 hours. Therefore, the system SHOULD trigger sleep (return True).
    assert is_host_asleep(idle_hours_threshold=4.0) is True
