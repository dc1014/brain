from System.organs.mirror_neurons import observe_human_behavior


def test_mirror_neurons_observation(monkeypatch, tmp_path):
    """Proves Mirror Neurons scan code, extract style, and stage mutations."""

    # 1. Sandbox setup
    root = tmp_path
    monkeypatch.setattr("System.organs.mirror_neurons.ROOT_DIR", root)
    monkeypatch.setattr(
        "System.organs.mirror_neurons.CONFIG_PATH",
        root / "System" / "config" / "agents.yaml",
    )

    mutations_file = root / "Meta" / "Mutations.md"
    monkeypatch.setattr("System.organs.mirror_neurons.MUTATIONS_PATH", mutations_file)

    # 2. Create mock human code
    studio_dir = root / "Studio" / "test_project"
    studio_dir.mkdir(parents=True)
    (studio_dir / "main.py").write_text(
        "def my_func():\n    '''Always use docstrings'''\n    pass"
    )

    # 3. Mock the LLM to output a mutation
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
                                    "content": '<neuroplasticity agent="product_manager">Use Python docstrings.</neuroplasticity>'
                                },
                            )()
                        },
                    )()
                ]
            },
        )(),
    )

    # 4. Execute
    observe_human_behavior("test_project")

    # 5. Assertions
    assert mutations_file.exists(), "Mutations file was not created!"
    staged_content = mutations_file.read_text()
    assert "Use Python docstrings" in staged_content, (
        "The stylistic mutation was not staged!"
    )
