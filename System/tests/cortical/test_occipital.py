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
