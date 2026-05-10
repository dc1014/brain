from System.organs.proprioception import (
    start_process,
    stop_process,
    list_processes,
    _save_state,
)


def test_proprioception_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "System.organs.proprioception.STATE_FILE", tmp_path / "motor_state.json"
    )

    # Use a perfectly cross-platform headless command
    cmd = 'python -c "import time; time.sleep(10)"'

    # 1. Start safely
    assert "SUCCESS" in start_process("test_sleep", cmd)
    assert "test_sleep" in list_processes()

    # 2. Block duplicates
    # FIX: Assert the new, accurate error message
    assert "already running" in start_process("test_sleep", cmd)

    # 3. Stop process
    assert "SUCCESS" in stop_process("test_sleep")
    assert "test_sleep" not in list_processes()


def test_proprioception_zombie_healing(monkeypatch, tmp_path):
    state_file = tmp_path / "motor_state.json"
    monkeypatch.setattr("System.organs.proprioception.STATE_FILE", state_file)

    # Manually inject a fake PID (999999) into the state file to simulate a crashed zombie
    fake_state = {
        "zombie_server": {"pid": 999999, "command": "npm run dev", "cwd": "root"}
    }
    _save_state(fake_state)

    # When list_processes is called, it should realize 999999 is dead, and auto-delete it.
    running = list_processes()

    # FIX: Assert the new descriptive Wernicke-friendly output
    assert "Cleaned up 1 dead processes" in running
