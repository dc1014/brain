from System.organs.basal_ganglia import (
    form_habit,
    break_habit,
    tick_habits,
    _load_habits,
)


def test_form_and_break_habit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "System.organs.basal_ganglia.HABITS_FILE", tmp_path / "habits.json"
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
        "System.organs.basal_ganglia.HABITS_FILE", tmp_path / "habits.json"
    )

    result = form_habit("evil_cron", "rm -rf /", 10)
    assert "AMYGDALA BLOCK" in result
    assert "evil_cron" not in _load_habits()


def test_tick_habits_execution(monkeypatch, tmp_path, mocker):
    monkeypatch.setattr(
        "System.organs.basal_ganglia.HABITS_FILE", tmp_path / "habits.json"
    )

    # Form a habit
    form_habit("quick_pulse", "echo hello", 1)

    # Mock subprocess to prove it gets called
    mock_popen = mocker.patch("System.organs.basal_ganglia.subprocess.Popen")

    # Tick 1: Should run immediately because last_run is 1970
    tick_habits()
    assert mock_popen.called
    mock_popen.reset_mock()

    # Tick 2: Should NOT run because 1 minute hasn't passed
    tick_habits()
    assert not mock_popen.called
