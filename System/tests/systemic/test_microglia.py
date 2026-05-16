import pytest
from System.neuroanatomy.systemic.microglia import trigger_immune_response_async


@pytest.mark.asyncio
async def test_microglia_successful_heal(monkeypatch, tmp_path):
    """Proves the immune system can intercept a failure, generate a patch, and retry successfully via Asyncio."""

    # 1. Mock the LLM to return a cross-platform valid fix command
    async def mock_acompletion(*args, **kwargs):
        return type(
            "Mock",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "message": type(
                                "Msg",
                                (),
                                {
                                    "content": f"python -c \"open('{tmp_path.as_posix()}/missing_file.txt', 'w').close()\""
                                },
                            )()
                        },
                    )()
                ]
            },
        )()

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.microglia.acompletion", mock_acompletion
    )

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.microglia.scan_command", lambda x: (True, "Safe")
    )

    # 2. Trigger an intentional failure (reading a file that doesn't exist using python)
    failed_cmd = (
        f"python -c \"open('{tmp_path.as_posix()}/missing_file.txt', 'r').read()\""
    )
    initial_stderr = "FileNotFoundError: No such file or directory: 'missing_file.txt'"

    # 3. Activate Microglia Asynchronously
    healed, output = await trigger_immune_response_async(
        failed_cmd, initial_stderr, str(tmp_path)
    )

    # 4. Assertions
    assert healed is True
    assert "autonomously applied a patch" in output
    assert (tmp_path / "missing_file.txt").exists(), (
        "The Microglia failed to execute the antibody!"
    )


@pytest.mark.asyncio
async def test_microglia_failed_heal(monkeypatch, tmp_path):
    """Proves the async immune system gracefully fails if the antibody doesn't work."""

    async def mock_acompletion(*args, **kwargs):
        return type(
            "Mock",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {"message": type("Msg", (), {"content": 'python -c "pass"'})()},
                    )()
                ]
            },
        )()

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.microglia.acompletion", mock_acompletion
    )

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.microglia.scan_command", lambda x: (True, "Safe")
    )

    failed_cmd = 'python -c "import nonexistent_module_12345"'
    initial_stderr = "ModuleNotFoundError: No module named 'nonexistent_module_12345'"

    healed, output = await trigger_immune_response_async(
        failed_cmd, initial_stderr, str(tmp_path)
    )

    assert healed is False
    assert "Microglia exhausted max retries" in output
