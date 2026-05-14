import base64
from System.neuroanatomy.cortical.occipital import (
    _encode_image_to_base64,
    perceive_image,
)
from unittest.mock import MagicMock


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


def test_video_security_size_limit(tmp_path):
    """Proves the Occipital Lobe blocks videos larger than 50MB."""
    from System.neuroanatomy.cortical.occipital import _validate_video_security

    fake_video = tmp_path / "massive.mp4"
    # Write exactly 50MB + 1 byte of junk data
    fake_video.write_bytes(b"0" * (50 * 1024 * 1024 + 1))

    result = _validate_video_security(fake_video)
    assert "SECURITY BLOCK: Video exceeds 50MB limit" in result


def test_video_security_magic_bytes_invalid(tmp_path):
    """Proves the OS catches malicious scripts disguised with an .mp4 extension."""
    from System.neuroanatomy.cortical.occipital import _validate_video_security

    fake_video = tmp_path / "malware.mp4"
    # Write a bash script payload instead of a real video header
    fake_video.write_bytes(b"#!/bin/bash\nrm -rf /")

    result = _validate_video_security(fake_video)
    assert "SECURITY BLOCK: Invalid magic bytes" in result


def test_video_security_magic_bytes_valid(tmp_path):
    """Proves the OS allows mathematically valid MP4 files."""
    from System.neuroanatomy.cortical.occipital import _validate_video_security

    fake_video = tmp_path / "safe.mp4"
    # Write a mathematically accurate minimal MP4 header (contains 'ftyp')
    fake_video.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00")

    result = _validate_video_security(fake_video)
    assert result is None  # None means it passed the security membrane!


def test_perceive_video_mocked_extraction(tmp_path, monkeypatch):
    """Proves the Occipital Lobe routes safe files to the Retina and LLM without burning API tokens."""
    from System.neuroanatomy.cortical.occipital import perceive_video
    from unittest.mock import MagicMock

    fake_video = tmp_path / "safe.mp4"
    fake_video.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00")

    # 1. Mock the Retina (Hardware Extraction)
    mock_extract = MagicMock(
        return_value=["data:image/jpeg;base64,frame1", "data:image/jpeg;base64,frame2"]
    )
    monkeypatch.setattr("Sense.receptors.vision.extract_video_frames", mock_extract)

    # 2. Mock the LLM (Cognitive Synthesis)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "A fox running in the snow."
    mock_completion = MagicMock(return_value=mock_response)
    monkeypatch.setattr("litellm.completion", mock_completion)

    # 3. Mock the Immune System Vault to prevent missing key errors
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

    result = perceive_video(str(fake_video), "What is happening?")

    # 4. Assertions
    assert "VISUAL ANALYSIS:" in result
    assert "fox running" in result
    mock_extract.assert_called_once_with(str(fake_video), max_frames=8)
    mock_completion.assert_called_once()
