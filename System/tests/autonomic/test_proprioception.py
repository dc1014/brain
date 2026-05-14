import time
from System.tools import ROOT_DIR
from System.neuroanatomy.autonomic.proprioception import (
    start_process,
    stop_process,
    list_processes,
)


def test_proprioception_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "System.neuroanatomy.autonomic.proprioception.STATE_FILE",
        tmp_path / "motor_state.json",
    )

    # Safely ensure the Studio directory exists for the CI runner
    (ROOT_DIR / "Studio").mkdir(exist_ok=True)

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

    # FIX: Windows occasionally keeps PIDs alive in the kernel.
    # Mock psutil to guarantee the OS sees it as dead, perfectly testing the OS healing logic.
    import psutil

    monkeypatch.setattr(psutil, "pid_exists", lambda pid: False)

    # list_processes autonomously cleans up dead processes!
    active = list_processes()
    assert "ghost_process" not in active
