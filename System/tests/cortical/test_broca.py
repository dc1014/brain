from System.neuroanatomy.cortical.broca import validate_qa_audit
from pydantic import BaseModel, Field
from System.neuroanatomy.cortical.broca import enforce_data_contract


def test_broca_perfect_articulation():
    response = "Here are my thoughts.\n<execute>\nrun_tests\n</execute>"
    is_valid, content = enforce_data_contract(response, "execute")
    assert is_valid is True
    assert content == "run_tests"


def test_broca_auto_heals_markdown_bleeding():
    fence = chr(96) * 3
    response = f"<execute>\n{fence}bash\nnpm run dev\n{fence}\n</execute>"
    is_valid, content = enforce_data_contract(response, "execute")
    assert is_valid is True
    assert content == "npm run dev"


def test_broca_valid_json_contract():
    response = '<schema>\n{"action": "build", "retries": 3}\n</schema>'
    is_valid, content = enforce_data_contract(response, "schema", expect_json=True)
    assert is_valid is True
    assert content["action"] == "build"


def test_broca_heals_json_trailing_comma():
    response = '<schema>\n{"action": "build", "retries": 3,}\n</schema>'
    is_valid, content = enforce_data_contract(response, "schema", expect_json=True)
    assert is_valid is True
    assert content["retries"] == 3


class SwarmAgentContract(BaseModel):
    name: str
    role: str
    confidence: float = Field(ge=0.0, le=1.0)


def test_broca_json_contract_with_markdown_bleeding():
    """Proves Broca isolates clean JSON structure from markdown blocks without XML tags."""
    fence = chr(96) * 3
    raw_llm_output = (
        "Here is the data you requested:\n"
        f"{fence}json\n"
        "{\n"
        '  "name": "Architect",\n'
        '  "role": "Planner",\n'
        '  "confidence": 0.95\n'
        "}\n"
        f"{fence}\n"
        "Let me know if you need anything else!"
    )

    # Passing the Pydantic model directly to enforce_data_contract
    result = enforce_data_contract(raw_llm_output, SwarmAgentContract)

    assert isinstance(result, SwarmAgentContract)
    assert result.name == "Architect"
    assert result.confidence == 0.95


def test_broca_qa_audit_pass():
    # Hiding the triple backticks from the UI parser using string math
    fence = "`" * 3
    response = (
        fence
        + "json\n"
        + '{"audit_result": "PASS", "reasoning": "Looks perfect."}\n'
        + fence
    )

    is_valid, msg = validate_qa_audit(response)
    assert is_valid is True
    assert msg == "PASS"


def test_broca_qa_audit_fail():
    response = '{"audit_result": "FAIL", "reasoning": "Missing unit tests."}'
    is_valid, msg = validate_qa_audit(response)

    assert is_valid is False
    assert (
        "CRITICAL - AUDIT FAILED. Read the critique, fix the instructions, and redeploy:\n\nMissing unit tests."
        in msg
    )


def test_broca_qa_audit_hallucination():
    response = "I think the code is good! I give it a PASS."
    is_valid, msg = validate_qa_audit(response)

    assert is_valid is False
    assert "BROCA FORMATTING ERROR" in msg
