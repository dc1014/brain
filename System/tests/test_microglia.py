from System.organs.microglia import trigger_immune_response


def test_microglia_successful_heal(monkeypatch, tmp_path):
    """Proves the immune system can intercept a failure, generate a patch, and retry successfully."""

    # 1. Mock the LLM to return a cross-platform valid fix command
    monkeypatch.setattr(
        "System.organs.microglia.completion",
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
                                    "content": "python -c \"open('missing_file.txt', 'w').close()\""
                                },
                            )()
                        },
                    )()
                ]
            },
        )(),
    )

    monkeypatch.setattr("System.organs.microglia.is_safe_path", lambda x: True)

    # 2. Trigger an intentional failure (reading a file that doesn't exist using python)
    failed_cmd = "python -c \"open('missing_file.txt', 'r').read()\""
    initial_stderr = "FileNotFoundError: No such file or directory: 'missing_file.txt'"

    # 3. Activate Microglia
    healed, output = trigger_immune_response(failed_cmd, initial_stderr, str(tmp_path))

    # 4. Assertions
    assert healed is True
    assert "Microglia (Immune System) detected an error" in output
    assert (tmp_path / "missing_file.txt").exists(), (
        "The Microglia failed to execute the antibody!"
    )


def test_microglia_failed_heal(monkeypatch, tmp_path):
    """Proves the immune system gracefully fails if the antibody doesn't work."""

    # Mock LLM to return a useless fix
    monkeypatch.setattr(
        "System.organs.microglia.completion",
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

    monkeypatch.setattr("System.organs.microglia.is_safe_path", lambda x: True)

    failed_cmd = 'python -c "import nonexistent_module_12345"'
    initial_stderr = "ModuleNotFoundError: No module named 'nonexistent_module_12345'"

    healed, output = trigger_immune_response(failed_cmd, initial_stderr, str(tmp_path))

    assert healed is False
    assert "Microglia exhausted max retries" in output
