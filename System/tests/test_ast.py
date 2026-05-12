from System.ast_parser import get_parser, extract_signatures, generate_project_stub


def test_get_parser():
    """Ensure the engine correctly maps file extensions to Tree-Sitter grammars."""
    assert get_parser(".py") is not None
    assert get_parser(".js") is not None
    assert get_parser(".tsx") is not None
    assert get_parser(".ts") is not None
    assert get_parser(".txt") is None


def test_extract_python_signatures(tmp_path) -> None:
    """Ensure the AST extractor correctly stubs out logic bodies."""
    py_file = tmp_path / "main.py"
    py_file.write_text(
        "class Database:\n"
        "    def connect(self, uri: str) -> bool:\n"
        "        # Heavy logic here\n"
        "        print('connecting')\n"
        "        return True\n",
        encoding="utf-8",
    )

    result = extract_signatures(str(py_file))

    assert "class Database:" in result
    assert "def connect(self, uri: str) -> bool:" in result
    assert "print('connecting')" not in result
    assert "return True" not in result
    assert "..." in result


def test_extract_typescript_signatures(tmp_path):
    """Ensure it extracts TS/JS structural definitions and arrow functions."""
    ts_file = tmp_path / "app.ts"
    ts_file.write_text(
        "export class Engine {\n"
        "  start() {\n"
        "    console.log('Vroom');\n"
        "  }\n"
        "}\n"
        "\n"
        "export const helper = () => {\n"
        "  return false;\n"
        "};\n",
        encoding="utf-8",
    )

    result = extract_signatures(str(ts_file))

    assert "class Engine" in result
    assert "start()" in result
    assert "const helper = () =>" in result
    assert "console.log('Vroom')" not in result


def test_generate_project_stub(tmp_path):
    """Ensure the directory walker correctly concatenates an entire repository."""
    # Setup mock src directory
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (src_dir / "api.py").write_text("def fetch_data():\n    pass\n", encoding="utf-8")

    # Broken into multiple lines to satisfy Ruff E501
    (src_dir / "ui.tsx").write_text(
        "export function Button() {\n  return null;\n}\n", encoding="utf-8"
    )

    # Setup ignored directory
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "junk.js").write_text("function ignoreMe() {}", encoding="utf-8")

    result = generate_project_stub(str(tmp_path))

    # Assert it found the valid files and built the headers
    assert "--- src" in result
    assert "api.py" in result
    assert "ui.tsx" in result

    # Assert it extracted the signatures
    assert "def fetch_data():" in result
    assert "function Button()" in result  # pure declaration drops the export wrapper

    # Assert it ignored node_modules
    assert "ignoreMe" not in result
