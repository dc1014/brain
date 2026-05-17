from System.organs.mirror_neurons import observe_human_behavior


def test_mirror_neurons_code_observation(monkeypatch, tmp_path):
    """Proves Mirror Neurons scan code, extract style, and stage mutations."""

    root = tmp_path
    monkeypatch.setattr("System.organs.mirror_neurons.ROOT_DIR", root)
    monkeypatch.setattr(
        "System.organs.mirror_neurons.CONFIG_PATH",
        root / "System" / "config" / "agents.yaml",
    )

    # Bypass safety path check for tmp_path testing
    monkeypatch.setattr("System.organs.mirror_neurons.is_safe_path", lambda x: True)

    mutations_file = root / "Meta" / "Mutations.md"
    monkeypatch.setattr("System.organs.mirror_neurons.MUTATIONS_PATH", mutations_file)

    studio_dir = root / "Studio" / "test_project"
    studio_dir.mkdir(parents=True)
    (studio_dir / "main.py").write_text("def my_func():\n    pass")

    monkeypatch.setattr(
        "System.organs.mirror_neurons.completion",
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
                                    "content": '<neuroplasticity agent="product_manager">Code Style</neuroplasticity>'
                                },
                            )()
                        },
                    )()
                ]
            },
        )(),
    )

    observe_human_behavior("Studio/test_project", is_writing=False)
    assert mutations_file.exists()
    assert "Code Style" in mutations_file.read_text()


def test_mirror_neurons_writing_observation(monkeypatch, tmp_path):
    """Proves Mirror Neurons can observe prose safely using an exact file path."""

    root = tmp_path
    monkeypatch.setattr("System.organs.mirror_neurons.ROOT_DIR", root)
    monkeypatch.setattr(
        "System.organs.mirror_neurons.CONFIG_PATH",
        root / "System" / "config" / "agents.yaml",
    )
    monkeypatch.setattr("System.organs.mirror_neurons.is_safe_path", lambda x: True)

    mutations_file = root / "Meta" / "Mutations.md"
    monkeypatch.setattr("System.organs.mirror_neurons.MUTATIONS_PATH", mutations_file)

    # Create a personal writing file
    personal_dir = root / "Personal"
    personal_dir.mkdir()
    writing_file = personal_dir / "journal.md"
    writing_file.write_text(
        "This is my private journal. I write in short sentences. Very punchy."
    )

    monkeypatch.setattr(
        "System.organs.mirror_neurons.completion",
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
                                    "content": '<neuroplasticity agent="dispatcher">Writing Style: Punchy.</neuroplasticity>'
                                },
                            )()
                        },
                    )()
                ]
            },
        )(),
    )

    # Execute observation on the specific file
    observe_human_behavior(str(writing_file.relative_to(root)), is_writing=True)

    staged_content = mutations_file.read_text()
    assert "Writing Style: Punchy" in staged_content
