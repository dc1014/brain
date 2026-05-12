import json
import sqlite3
import zipfile
from Sense.receptors.taste import sample_file


def test_taste_poison_rejector(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("AWS_KEY=12345")
    data = sample_file(str(env_file))
    assert data["format_type"] == "indigestible"
    assert "POISON DETECTED" in data["content_sample"]


def test_taste_api_sommelier(tmp_path):
    swagger = tmp_path / "swagger.json"
    spec = {"paths": {"/users": {"get": {"summary": "Get all users"}}}}
    swagger.write_text(json.dumps(spec))
    data = sample_file(str(swagger))
    assert data["format_type"] == "api_spec"
    assert "GET /users - Get all users" in data["content_sample"]


def test_taste_office_umami(tmp_path):
    docx = tmp_path / "test.docx"
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr("word/document.xml", "<w:t>Hello</w:t><w:t>World</w:t>")
    data = sample_file(str(docx))
    assert data["format_type"] == "office_document"
    assert "Hello World" in data["content_sample"]


def test_taste_base64_gag_reflex_ipynb(tmp_path):
    ipynb = tmp_path / "test.ipynb"
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["print(1)"],
                "outputs": [{"data": {"image/png": "iVBORw0KGgo..."}}],
            }
        ]
    }
    ipynb.write_text(json.dumps(notebook))
    data = sample_file(str(ipynb))
    assert data["format_type"] == "jupyter_notebook"
    assert "BASE64 IMAGE OMITTED FOR TOKEN SAFETY" in data["content_sample"]


def test_taste_gag_reflex(tmp_path):
    exe_file = tmp_path / "virus.exe"
    exe_file.write_bytes(b"MZ\x90\x00")
    data = sample_file(str(exe_file))
    assert data["format_type"] == "indigestible"
    assert "GAG REFLEX" in data["content_sample"]


def test_taste_crunchy_zip(tmp_path):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("folder/file1.txt", "data")
        z.writestr("folder/file2.txt", "data")

    data = sample_file(str(zip_path))
    assert data["format_type"] == "archive_manifest"
    assert "folder/file1.txt" in data["content_sample"]


def test_taste_sqlite_memory(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    conn.close()

    data = sample_file(str(db_path))
    assert data["format_type"] == "database_schema"
    assert "CREATE TABLE users" in data["content_sample"]


def test_taste_bitter_log_distillation(tmp_path):
    log_path = tmp_path / "server.log"
    log_path.write_text("INFO: all good\nERROR: crash\nFATAL: dead")
    data = sample_file(str(log_path))
    assert "INFO" not in data["content_sample"]
    assert "ERROR: crash" in data["content_sample"]


def test_taste_ast_code_skeleton(tmp_path):
    py_file = tmp_path / "app.py"
    py_file.write_text(
        "class Server:\\n    def start(self):\\n        print('running')\\n"
    )
    data = sample_file(str(py_file))
    assert data["format_type"] == "code_skeleton"
    assert "class Server:" in data["content_sample"]
    assert "def start(self):" in data["content_sample"]
    # Verify the deep logic is stripped!
    assert "print('running')" not in data["content_sample"]


def test_taste_media_metadata(tmp_path):
    import struct

    png_file = tmp_path / "test.png"
    # Create a valid fake PNG header with width 100, height 50
    png_file.write_bytes(
        b"\\x89PNG\\r\\n\\x1a\\n" + b"\\x00" * 16 + struct.pack(">II", 100, 50)
    )

    data = sample_file(str(png_file))
    assert data["format_type"] == "media_metadata"
    assert "100x50 pixels" in data["content_sample"]
    assert "Type: Binary Media (.png)" in data["content_sample"]


def test_taste_semantic_csv_markdown(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name,role\\n1,Alice,Admin\\n2,Bob,User")

    data = sample_file(str(csv_file))
    assert data["format_type"] == "structured_data"
    assert "| id | name | role |" in data["content_sample"]
    assert "|---|---|---|" in data["content_sample"].replace(" ", "")
    assert "| 1 | Alice | Admin |" in data["content_sample"]
