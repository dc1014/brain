import base64
from System.neuroanatomy.cortical.occipital import (
    _encode_image_to_base64,
    perceive_image,
)


def test_occipital_encodes_base64(tmp_path):
    # Create a fake tiny image
    img_path = tmp_path / "test.png"
    fake_data = b"fake_image_bytes"
    img_path.write_bytes(fake_data)

    encoded = _encode_image_to_base64(str(img_path))
    assert encoded == base64.b64encode(fake_data).decode("utf-8")


def test_occipital_handles_missing_file():
    result = perceive_image("does_not_exist.png", "What is this?")
    assert "VISUAL ERROR" in result
    assert "does not exist" in result


def test_generate_visual_asset_missing_key(monkeypatch):
    """Ensures a missing API key triggers the Motor Cortex circuit breaker."""
    from System.neuroanatomy.cortical.occipital import generate_visual_asset

    # Force vault and environment to be empty
    monkeypatch.setattr(
        "System.neuroanatomy.systemic.immune_system.vault.get_api_key_for_model",
        lambda x: None,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = generate_visual_asset("A fox", "test.png")
    assert "SECURITY BLOCK: OPENAI_API_KEY is missing" in result


def test_generate_visual_asset_api_error(monkeypatch):
    """Ensures that OpenAI HTTP rejections are caught and converted to a SECURITY BLOCK."""
    from System.neuroanatomy.cortical.occipital import generate_visual_asset
    import urllib.error
    from unittest.mock import MagicMock

    monkeypatch.setattr(
        "System.neuroanatomy.systemic.immune_system.vault.get_api_key_for_model",
        lambda x: "sk-fake",
    )
    monkeypatch.setattr(
        "System.neuroanatomy.cortical.occipital.Path.mkdir", MagicMock()
    )

    def mock_urlopen(*args, **kwargs):
        error = urllib.error.HTTPError(
            url="https://api.openai.com/v1/images/generations",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=None,
        )
        error.read = MagicMock(
            return_value=b'{"error": {"message": "Model not found"}}'
        )
        raise error

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    result = generate_visual_asset("A fox", "test.png")
    assert "SECURITY BLOCK: OpenAI rejected the request" in result
    assert "Model not found" in result
