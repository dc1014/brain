import json
from System.core.orchestrator import run_pending_queue


def test_run_pending_queue_thalamic_routing_sync(mocker, tmp_path, monkeypatch):
    """
    Zero-Debt Test: Proves that background Obsidian tasks correctly route through
    the Thalamic `dispatch_task` matrix instead of bypassing directly to the PFC.
    """
    # 1. Setup isolated memory space
    monkeypatch.setattr("System.core.orchestrator.ROOT_DIR", tmp_path)

    meta_dir = tmp_path / "Meta"
    meta_dir.mkdir()

    queue_file = meta_dir / "queue.jsonl"
    approved_flag = meta_dir / ".approved"

    # 2. Mock a pending user task waiting in the Obsidian background queue
    payload = {
        "prompt": "Analyze the systemic logs",
        "route": "TERMINAL",
        "domain": "STUDIO",
    }
    queue_file.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    # Drop the dopamine approval flag to trigger execution
    approved_flag.touch()

    # 3. Mock dispatch_task so we don't accidentally fire up live LLM inference threads
    mock_dispatch = mocker.patch("System.core.orchestrator.dispatch_task")

    # 4. Execute the background queue consumer
    run_pending_queue()

    # 5. Strict Validation
    # Ensure the dopamine approval flag was safely consumed
    assert not approved_flag.exists(), (
        "Bug: The approval flag was not consumed, causing an infinite execution loop!"
    )

    # Ensure the queue file was wiped clean
    assert queue_file.read_text(encoding="utf-8") == "", (
        "Bug: The queue file was not cleared after reading!"
    )

    # Ensure Thalamic routing bypass was successfully hit with the correct parameters
    mock_dispatch.assert_called_once_with(
        "Analyze the systemic logs",
        obsidian=True,
        predefined_route="TERMINAL",
        predefined_domain="STUDIO",
    )
