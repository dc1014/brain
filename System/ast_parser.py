import os
from typing import Any

# ⚡ SHIFT-LEFT: Safely check for optional parsing binaries and gracefully fallback
try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript

    TREE_SITTER_AVAILABLE = True

    # Explicitly type-annotate as Any to allow safe fallback assignment without triggering Mypy errors
    LANG_PY: Any = Language(tspython.language())
    LANG_JS: Any = Language(tsjavascript.language())
    LANG_TS: Any = Language(tstypescript.language_typescript())
    LANG_TSX: Any = Language(tstypescript.language_tsx())

except Exception:
    TREE_SITTER_AVAILABLE = False
    LANG_PY = LANG_JS = LANG_TS = LANG_TSX = None


def get_parser(extension: str) -> Any:
    """Returns the correct Tree-Sitter parser based on file extension."""
    if not TREE_SITTER_AVAILABLE:
        return None

    lang = None
    if extension == ".py":
        lang = LANG_PY
    elif extension in [".js", ".jsx"]:
        lang = LANG_JS
    elif extension == ".ts":
        lang = LANG_TS
    elif extension == ".tsx":
        lang = LANG_TSX
    else:
        return None

    # Safely handles both Tree-sitter v0.21 and v0.22+ API changes for all setups
    try:
        parser = Parser(lang)  # type: ignore
    except TypeError:
        parser = Parser()  # type: ignore
        try:
            parser.set_language(lang)  # type: ignore
        except AttributeError:
            parser.language = lang  # type: ignore

    return parser


def extract_signatures(file_path: str) -> str:
    """Parses a file and extracts only structural signatures (classes, functions)."""
    ext = os.path.splitext(file_path)[1]
    parser = get_parser(ext)

    if not parser:
        return ""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception:
        return ""

    tree = parser.parse(bytes(source_code, "utf8"))

    # Explicitly type annotate stubs list to avoid LiteralString type inference constraints
    stubs: list[str] = []

    def walk(node: Any, depth: int = 0) -> None:
        indent = "  " * depth

        if node.type in [
            "class_definition",  # Python class
            "function_definition",  # Python def
            "class_declaration",  # TS/JS class
            "method_definition",  # TS/JS class method
            "function_declaration",  # TS/JS function
            "lexical_declaration",  # TS/JS let/const (arrow functions)
            "variable_declaration",  # TS/JS var (arrow functions)
        ]:
            block_node = None

            # Breadth-First Search to find the body block (handles deeply nested TS/JS arrow functions)
            queue = list(node.children)
            while queue:
                child = queue.pop(0)
                if child.type in ["block", "statement_block", "class_body"]:
                    block_node = child
                    break
                if child.type in ["variable_declarator", "arrow_function"]:
                    queue.extend(child.children)

            if block_node:
                sig_bytes = bytes(source_code, "utf8")[
                    node.start_byte : block_node.start_byte
                ]
                signature = sig_bytes.decode("utf-8").strip()

                if signature.endswith("{"):
                    signature = signature[:-1].strip()

                stubs.append(f"{indent}{signature} ...")

                if node.type in ["class_definition", "class_declaration"]:
                    for child in block_node.children:
                        walk(child, depth + 1)
            return

        for child in node.children:
            walk(child, depth)

    walk(tree.root_node)
    return "\n".join(stubs)


def generate_project_stub(directory: str) -> str:
    """Walks a directory and returns a concatenated map of all file signatures."""
    if not TREE_SITTER_AVAILABLE:
        return "Project parsing unavailable. Tree-sitter syntax module not installed."

    project_stub: list[str] = []
    ignored_dirs = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]

        for file in files:
            if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory)

                signatures = extract_signatures(file_path)
                if signatures:
                    project_stub.append(f"--- {rel_path} ---\n{signatures}\n")

    return "\n".join(project_stub)
