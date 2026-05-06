def test_extract_python_signatures() -> None:
    """Ensure the AST extractor correctly stubs out logic bodies."""
    from System.ast_parser import extract_python_signatures

    test_code = (
        "class Database:\n"
        "    def connect(self, uri: str) -> bool:\n"
        "        # Heavy logic here\n"
        "        print('connecting')\n"
        "        return True\n"
    )

    result = extract_python_signatures(test_code)

    # 1. Check that the signatures survived
    assert "class Database:" in result
    assert "def connect(self, uri: str) -> bool:" in result

    # 2. Check that the logic was destroyed
    assert "print('connecting')" not in result
    assert "return True" not in result

    # 3. Check that the stub indicator was injected
    assert "..." in result
