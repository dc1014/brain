from pydantic import BaseModel, Field
from System.neuroanatomy.cortical.broca import enforce_data_contract


def test_broca_perfect_articulation():
    response = "Here are my thoughts.\n<execute>\nrun_tests\n</execute>"
    is_valid, content = enforce_data_contract(response, "execute")
    assert is_valid is True
    assert content == "run_tests"


def test_broca_auto_heals_markdown_bleeding():
    response = "<execute>\n```bash\nnpm run dev\n```\n</execute>"
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
    raw_llm_output = (
        "Here is the data you requested:\n"
        "```json\n"
        "{\n"
        '    "name": "Data_Engineer",\n'
        '    "role": "Data_Science",\n'
        '    "confidence": 0.88\n'
        "}\n"
        "```"
    )

    agent = enforce_data_contract(raw_llm_output, SwarmAgentContract)
    assert isinstance(agent, SwarmAgentContract)
    assert agent.name == "Data_Engineer"
    assert agent.confidence == 0.88
