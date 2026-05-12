import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# 1. Load the Language Grammar
PY_LANGUAGE = Language(tspython.language())

# 2. Initialize the Parser
parser = Parser(PY_LANGUAGE)


def extract_python_signatures(file_content: str) -> str:
    """Parses a Python file and extracts only class and function signatures."""
    raw_bytes = bytes(file_content, "utf-8")
    tree = parser.parse(raw_bytes)

    stubs = []

    def walk(node, depth=0):
        indent = "    " * depth

        if node.type in ["class_definition", "function_definition"]:
            # Find the 'block' node (the actual body of the class or function)
            block_node = next(
                (child for child in node.children if child.type == "block"), None
            )

            if block_node:
                # AST BYTE SLICE: Grab everything from 'class'/'def' up to the start of the body
                sig_bytes = raw_bytes[node.start_byte : block_node.start_byte]
                signature = sig_bytes.decode("utf-8").strip()

                # Reassemble the stub with the correct indentation
                stubs.append(f"{indent}{signature}\n{indent}    ...")

                # If it's a class, we must walk INSIDE the body to find its methods!
                if node.type == "class_definition":
                    for child in block_node.children:
                        walk(child, depth + 1)

            # Stop walking down this branch (we drop nested functions to save context)
            return

        # If it's not a class or function, keep walking down the tree
        for child in node.children:
            walk(child, depth)

    walk(tree.root_node)
    return "\n\n".join(stubs) if stubs else "# No classes or functions found."
