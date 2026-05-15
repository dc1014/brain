from System.neuroanatomy.limbic.basal_ganglia import (
    form_habit,
    break_habit,
    tick_habits,
    _load_habits,
)


def test_form_and_break_habit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.basal_ganglia.HABITS_FILE", tmp_path / "habits.json"
    )

    # Form
    assert "SUCCESS" in form_habit("test_cleanup", "echo hello", 60)
    habits = _load_habits()
    assert "test_cleanup" in habits
    assert habits["test_cleanup"]["interval_minutes"] == 60

    # Break
    assert "SUCCESS" in break_habit("test_cleanup")
    assert "test_cleanup" not in _load_habits()


def test_amygdala_blocks_malicious_habits(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.basal_ganglia.HABITS_FILE", tmp_path / "habits.json"
    )

    result = form_habit("evil_cron", "rm -rf /", 10)
    assert "AMYGDALA BLOCK" in result
    assert "evil_cron" not in _load_habits()


def test_tick_habits_execution(monkeypatch, tmp_path, mocker):
    habits_file = tmp_path / "habits.json"
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.basal_ganglia.HABITS_FILE", habits_file
    )

    # 🛡️ THE MISSING LINK: Tell the Blood-Brain Barrier that our tmp_path is safe!
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        lambda x: (True, str(tmp_path)),
    )

    # Form a habit
    form_habit("quick_pulse", "echo hello", 1)

    # 🧬 BIOMIMETIC REWIND
    import json
    from datetime import datetime, timedelta

    data = json.loads(habits_file.read_text())

    # 1. Parse the exact timezone-aware format the OS generated
    last_run_dt = datetime.fromisoformat(data["quick_pulse"]["last_run"])

    # 2. Rewind it safely by 10 minutes
    rewound_dt = last_run_dt - timedelta(minutes=10)

    # 3. Write the mathematically perfect string back to disk
    data["quick_pulse"]["last_run"] = rewound_dt.isoformat()
    habits_file.write_text(json.dumps(data))

    # 🎯 ZERO DEBT FIX: Patch the entire subprocess module
    mock_subprocess = mocker.patch(
        "System.neuroanatomy.limbic.basal_ganglia.subprocess"
    )

    # Tick 1: Now parses successfully and detects the overdue habit
    tick_habits()

    # Verify the call through the parent mock
    assert mock_subprocess.Popen.called
    mock_subprocess.Popen.reset_mock()

    # Tick 2: Should NOT run because 1 minute hasn't passed
    tick_habits()
    assert not mock_subprocess.Popen.called
