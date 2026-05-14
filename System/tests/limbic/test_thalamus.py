from System.neuroanatomy.limbic.thalamus import filter_attention


def test_thalamus_fast_path():
    """Proves the Thalamus skips filtering if the memory is short enough."""
    short_memory = "This is a short memory."
    filtered = filter_attention("Build a react app", short_memory)

    # Should return exactly the original text (bypassing the LLM)
    assert filtered == short_memory


def test_thalamus_filtering(monkeypatch):
    """Proves the Thalamus correctly calls the LLM for large memories."""

    # Create a dummy memory large enough to trigger the Thalamus (> 2000 chars)
    large_memory = "A" * 2500

    # Mock the LLM to return a specific filtered string
    monkeypatch.setattr(
        "System.neuroanatomy.limbic.thalamus.completion",
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
                                "Msg", (), {"content": "Filtered React bullet point."}
                            )()
                        },
                    )()
                ]
            },
        )(),
    )

    filtered = filter_attention("Build a react app", large_memory)

    assert "FILTERED CONTEXT" in filtered
    assert "Filtered React bullet point." in filtered
