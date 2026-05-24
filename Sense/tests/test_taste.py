import json
import zipfile
from Sense.receptors.taste import sample_file


def test_taste_poison_rejector(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("AWS_KEY=12345")
    data = sample_file(env_file)
    assert data["format_type"] == "indigestible"
    assert "POISON DETECTED" in data["content_sample"]


def test_taste_api_sommelier(tmp_path):
    swagger = tmp_path / "swagger.json"
    # ⚡ FIX: Added "openapi" to trigger the dictionary schema detection
    spec = {
        "openapi": "3.0.0",
        "paths": {"/users": {"get": {"summary": "Get all users"}}},
    }
    swagger.write_text(json.dumps(spec))
    data = sample_file(swagger)
    assert data["format_type"] == "api_spec"
    assert "GET /users - Get all users" in data["content_sample"]


def test_taste_office_umami(tmp_path):
    docx = tmp_path / "test.docx"
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr("word/document.xml", "<w:t>Hello</w:t><w:t>World</w:t>")
    data = sample_file(docx)
    assert data["format_type"] == "office_document"
    assert "Hello" in data["content_sample"]
    assert "World" in data["content_sample"]


def test_taste_base64_gag_reflex_ipynb(tmp_path):
    notebook_file = tmp_path / "test.ipynb"
    # ⚡ FIX: Added "cell_type": "code" to trigger the image output parsing
    notebook_file.write_text(
        '{"cells": [{"cell_type": "code", "outputs": [{"data": {"image/png": "base64..."}}]}]}'
    )
    data = sample_file(notebook_file)
    assert data["format_type"] == "notebook"
    assert "BASE64" in data["content_sample"]
    assert "OMITTED" in data["content_sample"]


def test_taste_bitter_log_distillation(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("INFO: Starting\nERROR: Something broke\n")
    data = sample_file(log_file)
    assert data["format_type"] == "raw_text"
    assert "[LOG DISTILLATION: Extracted Errors]" in data["content_sample"]


def test_taste_ast_code_skeleton(tmp_path, mocker):
    py_file = tmp_path / "app.py"
    py_file.write_text(
        "class Server:\n    def start(self):\n        print('running')\n"
    )
    # ⚡ FIX: Mock extract_signatures to ensure pure unit test isolation
    mocker.patch(
        "Sense.receptors.taste.extract_signatures",
        return_value="class Server:\n    def start(self):",
    )
    data = sample_file(py_file)
    assert data["format_type"] == "code_skeleton"
    assert "class Server" in data["content_sample"]
    assert "def start(self):" in data["content_sample"]


def test_taste_media_metadata(tmp_path):
    import struct

    png_file = tmp_path / "test.png"
    png_file.write_bytes(
        b"\x89PNG\r\n\x1a\n" + b"\x00" * 16 + struct.pack(">II", 100, 50)
    )
    data = sample_file(png_file)
    assert data["format_type"] == "media_metadata"
    assert "[MEDIA METADATA TASTED]" in data["content_sample"]
    assert "Type: Binary Media (.png)" in data["content_sample"]


def test_taste_semantic_csv_markdown(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id,name,role\n1,Alice,Admin\n2,Bob,User\n")
    data = sample_file(csv_file)
    assert "Alice" in data["content_sample"]
    assert "Bob" in data["content_sample"]
