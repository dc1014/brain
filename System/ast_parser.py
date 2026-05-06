import os
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript

# 1. Initialize the Language Grammars
LANG_PY = Language(tspython.language())
LANG_JS = Language(tsjavascript.language())
LANG_TS = Language(tstypescript.language_typescript())
LANG_TSX = Language(tstypescript.language_tsx())


def get_parser(extension: str):
    """Returns the correct Tree-Sitter parser based on file extension."""
    parser = Parser(LANG_PY)  # Default fallback
    if extension == ".py":
        parser = Parser(LANG_PY)
    elif extension in [".js", ".jsx"]:
        parser = Parser(LANG_JS)
    elif extension == ".ts":
        parser = Parser(LANG_TS)
    elif extension == ".tsx":
        parser = Parser(LANG_TSX)
    else:
        return None
    return parser


def extract_signatures(file_path: str) -> str:
    """Parses a file and extracts only structural signatures (classes, functions)."""
    ext = os.path.splitext(file_path)[1].lower()
    parser = get_parser(ext)

    if not parser:
        return ""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return ""

    raw_bytes = bytes(content, "utf-8")
    tree = parser.parse(raw_bytes)
    stubs = []

    target_nodes = {
        "class_definition",
        "function_definition",  # Python
        "class_declaration",
        "function_declaration",
        "method_definition",  # JS/TS
        "lexical_declaration",  # JS/TS Const arrow functions
    }
    body_nodes = {"block", "statement_block", "class_body"}

    def walk(node, depth=0):
        indent = "    " * depth

        if node.type in target_nodes:
            # Helper to dig into variable declarators for arrow functions
            def find_body(n):
                for c in n.children:
                    if c.type in body_nodes:
                        return c
                    if c.type in ["variable_declarator", "arrow_function"]:
                        res = find_body(c)
                        if res:
                            return res
                return None

            block_node = find_body(node)

            if block_node:
                # AST BYTE SLICE: Grab the signature, ignore the body!
                sig_bytes = raw_bytes[node.start_byte : block_node.start_byte]
                signature = sig_bytes.decode("utf-8").strip()

                # Clean up trailing braces
                if signature.endswith("{"):
                    signature = signature[:-1].strip()

                stubs.append(f"{indent}{signature} ...")

                # If it's a class, walk inside to get its methods
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
    project_stub = []
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
