from pathlib import Path


def test_windows_setup_detects_python_launcher_versions():
    text = Path("setup.ps1").read_text(encoding="utf-8")
    assert "Resolve-PythonCandidate" in text
    assert '"-3.12"' in text
    assert '"-3.13"' in text
    assert '"-3.14"' in text
    assert "Microsoft\\WindowsApps\\python.exe" in text


def test_windows_setup_error_names_winget_fix():
    text = Path("setup.ps1").read_text(encoding="utf-8")
    assert "winget install Python.Python.3.12" in text
    assert ".\\setup.ps1 -Local" in text
    assert "start Docker Desktop" in text
