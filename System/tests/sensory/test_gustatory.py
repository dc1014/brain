from System.neuroanatomy.sensory.gustatory import process_taste_profile
from System.tools import taste_safe_file


def test_process_taste_profile(tmp_path, monkeypatch):
    monkeypatch.setattr("System.neuroanatomy.sensory.gustatory.ROOT_DIR", tmp_path)
    monkeypatch.setattr("System.tools.file_system.ROOT_DIR", tmp_path)
    monkeypatch.setattr("System.tools.sensory.is_safe_path", lambda x: True)

    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    # Test Organ
    xml = process_taste_profile("test.txt")
    assert "<taste_profile" in xml
    assert "Hello World" in xml

    # Test Tool
    tool_xml = taste_safe_file("test.txt")

    # 🎯 THE FIX: Explicitly check the .output property for exact equality
    assert tool_xml.output == xml
