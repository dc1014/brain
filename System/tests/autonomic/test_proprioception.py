import time
import os
from System.tools import ROOT_DIR
from System.neuroanatomy.autonomic.proprioception import (
    start_process,
    stop_process,
    list_processes,
    sweep_zombies,
    _save_state,
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

    # 2. Check state (Will no longer cannibalize itself)
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

    # Inject an orphan and a legitimate process
    _save_state(
        {
            "ghost_server": {
                "pid": 999999,
                "command": "npm run dev",
                "cwd": "/fake",
                "parent_pid": 999998,  # Fake dead parent
            },
            "my_server": {
                "pid": 999997,
                "command": "npm run build",
                "cwd": "/fake",
                "parent_pid": os.getpid(),  # Belongs to this exact active session
            },
        }
    )

    import psutil

    def mock_pid_exists(pid):
        if pid == 999998:  # Parent of ghost is dead
            return False
        return True  # The actual processes are "alive"

    monkeypatch.setattr(psutil, "pid_exists", mock_pid_exists)

    mocker.patch("psutil.Process")

    sweep_zombies()

    state = _load_state()

    # The ghost should be swept because its parent died
    assert "ghost_server" not in state
    # The active server should be swept because it belongs to US and sweep_zombies was called explicitly
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

    # ⚡ ZERO-DEBT: Fix F841 by removing the unused local variable assignment
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
