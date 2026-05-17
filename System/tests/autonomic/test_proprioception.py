import time
import os
import threading
from System.tools import ROOT_DIR
from System.neuroanatomy.autonomic.proprioception import (
    start_process,
    stop_process,
    list_processes,
    sweep_zombies,
    mutate_state,
    _load_state,
)


def test_proprioception_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.proprioception.STATE_FILE",
        tmp_path / "motor_state.json",
    )

    safe_dir = tmp_path / "Studio"
    safe_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        lambda x: (True, str(safe_dir)),
    )

    cmd = 'python -c "import time; time.sleep(10)"'

    # 1. Start safely
    assert "SUCCESS" in start_process("test_sleep", cmd)

    # 2. Check state
    status = list_processes()
    assert "test_sleep" in status

    # 3. Stop gracefully
    stop_result = stop_process("test_sleep")
    assert "SUCCESS" in stop_result

    # 4. Verify cleanup
    time.sleep(0.5)
    final_status = list_processes()
    assert "test_sleep" not in final_status


def test_proprioception_zombie_healing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.proprioception.STATE_FILE",
        tmp_path / "motor_state.json",
    )
    (ROOT_DIR / "Studio").mkdir(exist_ok=True)

    start_process("ghost_process", 'python -c "print(1)"')

    import psutil

    monkeypatch.setattr(psutil, "pid_exists", lambda pid: False)

    active = list_processes()
    assert "ghost_process" not in active


def test_proprioception_orphan_sweeping(monkeypatch, tmp_path, mocker):
    """Proves that sweep_zombies slaughters processes left behind by dead parents (hard crash)."""
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.proprioception.STATE_FILE",
        tmp_path / "motor_state.json",
    )

    with mutate_state() as state:
        state.clear()
        state.update(
            {
                "ghost_server": {
                    "pid": 999999,
                    "command": "npm run dev",
                    "cwd": "/fake",
                    "parent_pid": 999998,
                },
                "my_server": {
                    "pid": 999997,
                    "command": "npm run build",
                    "cwd": "/fake",
                    "parent_pid": os.getpid(),
                },
            }
        )

    import psutil

    def mock_pid_exists(pid):
        if pid == 999998:
            return False
        return True

    monkeypatch.setattr(psutil, "pid_exists", mock_pid_exists)

    mocker.patch("psutil.Process")

    sweep_zombies()

    state = _load_state()

    assert "ghost_server" not in state
    assert "my_server" not in state


def test_proprioception_tool_interface_with_port(monkeypatch, tmp_path):
    """Verifies that the tool interface safely accepts and handles port parameters."""
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.proprioception.STATE_FILE",
        tmp_path / "motor_state.json",
    )

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.blood_brain_barrier.validate_execution_path",
        lambda x: (True, str(tmp_path)),
    )

    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.proprioception.is_port_in_use", lambda port: True
    )

    from System.neuroanatomy.autonomic.proprioception import manage_background_process

    result = manage_background_process(
        action="start",
        name="test_port_service",
        command="python -m http.server",
        cwd=str(tmp_path),
        port=8000,
    )

    assert "SUCCESS" in result or "Success" in result


def test_proprioception_atomic_lock_concurrency(monkeypatch, tmp_path):
    """Proves that multiple fast-firing threads can mutate state without data corruption using mutate_state."""
    state_file = tmp_path / "motor_state.json"
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.proprioception.STATE_FILE",
        state_file,
    )

    with mutate_state() as initial_state:
        initial_state.clear()

    def worker_mutation(worker_id: int):
        for _ in range(5):
            with mutate_state() as locked_state:
                locked_state[f"worker_{worker_id}"] = {
                    "pid": worker_id,
                    "command": "mock",
                    "cwd": "/fake",
                }
            time.sleep(0.01)

    threads = [threading.Thread(target=worker_mutation, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final_state = _load_state()

    assert len(final_state) == 4
    for i in range(4):
        assert f"worker_{i}" in final_state
