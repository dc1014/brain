from System.neuroanatomy.systemic.microglia import trigger_immune_response


def test_microglia_successful_heal(monkeypatch, tmp_path):
    """Proves the immune system can intercept a failure, generate a patch, and retry successfully."""

    # 1. Mock the LLM to return a valid fix command
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.microglia.completion",
        lambda *args, **kwargs: type(
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
        )(),
    )

    # Mock Amygdala to pass the command
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.microglia.scan_command", lambda x: (True, "Safe")
    )

    # 2. Trigger an intentional failure (reading a file that doesn't exist)
    failed_cmd = (
        f"python -c \"open('{tmp_path.as_posix()}/missing_file.txt', 'r').read()\""
    )
    initial_stderr = "FileNotFoundError: No such file or directory"

    # 3. Activate Microglia
    healed, output = trigger_immune_response(failed_cmd, initial_stderr, str(tmp_path))

    # 4. Assertions
    assert healed is True
    assert "autonomously applied a patch" in output
    assert (tmp_path / "missing_file.txt").exists(), (
        "The Microglia failed to execute the antibody!"
    )


def test_microglia_failed_heal(monkeypatch, tmp_path):
    """Proves the immune system gracefully fails if the antibody doesn't work."""

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.microglia.completion",
        lambda *args, **kwargs: type(
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
        )(),
    )

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.microglia.scan_command", lambda x: (True, "Safe")
    )

    failed_cmd = 'python -c "import nonexistent_module_12345"'
    initial_stderr = "ModuleNotFoundError"

    healed, output = trigger_immune_response(failed_cmd, initial_stderr, str(tmp_path))

    assert healed is False
    assert "Microglia exhausted max retries" in output
