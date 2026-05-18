import os
from unittest.mock import MagicMock
from System.runtime import analyze_task


def test_analyze_task_deterministic_blocks() -> None:
    """Test that shift-left heuristics block illegal prompts before hitting the LLM."""
    from System.runtime import analyze_task

    # 1. Test the destructive action block
    is_valid, reason, route, domain, _ = analyze_task("Can you delete my journal?")
    assert is_valid is False
    assert "amygdala rule" in reason.lower()

    # 2. Test the vital organ protection (Sandboxing)
    is_valid, reason, route, domain, _ = analyze_task("Can you read the .env file?")
    assert is_valid is False
    assert "amygdala boundary" in reason.lower()


def test_analyze_task_llm_parsing(mocker) -> None:  # type: ignore
    """Test that the dispatcher correctly extracts ROUTE and DOMAIN from the LLM."""

    # --- Disable the Gut Reflex so the signal reaches the LLM ---
    mocker.patch("System.organs.enteric.get_gut_reaction", return_value=None)

    mock_completion = mocker.patch("System.runtime.completion")
    # ... rest of the function remains the same ...

    # Setup mock LLM response returning the exact format we demand
    msg = MagicMock()
    msg.content = "ROUTE: READ_ONLY\nDOMAIN: STUDIO"

    mock_response = MagicMock(choices=[MagicMock(message=msg)])
    # Mock the usage stats to prove token counting works
    mock_response.usage = MagicMock(
        prompt_tokens=10, completion_tokens=5, total_tokens=15
    )
    mock_completion.return_value = mock_response

    is_valid, reason, route, domain, usage = analyze_task("Search the Studio folder")

    assert is_valid is True
    assert route == "READ_ONLY"
    assert domain == "STUDIO"
    assert usage["total_tokens"] == 15


def test_analyze_task_llm_rejection(mocker) -> None:  # type: ignore
    """Test that the dispatcher correctly handles explicit REJECTED messages."""
    mock_completion = mocker.patch("System.runtime.completion")

    # Setup mock LLM response acting like it hit a limitation
    msg = MagicMock()
    msg.content = "REJECTED: I cannot browse the live internet."
    mock_completion.return_value = MagicMock(choices=[MagicMock(message=msg)])

    is_valid, reason, route, domain, _ = analyze_task(
        "Go to google.com and find the news."
    )

    assert is_valid is False
    # SHIFT-LEFT FIX: Account for the uppercase transformation in runtime.py
    assert "browse the live internet" in reason.lower()
    assert route == "NONE"


def test_analyze_task_api_error(mocker) -> None:  # type: ignore
    """Test that API errors during dispatch fail safely."""
    mock_completion = mocker.patch("System.runtime.completion")
    mock_completion.side_effect = Exception("Anthropic API is down.")

    is_valid, reason, route, domain, _ = analyze_task("Build me a website.")

    assert is_valid is False
    assert "Dispatcher API Error" in reason
    assert "Anthropic API is down" in reason
    assert route == "NONE"


def test_auditor_headless_retry_bypass(mocker):
    """Test that the headless flag auto-approves an Auditor retry without pausing."""
    from System.llm import AgentResponse
    from System.runtime import execute_pipeline

    # 1. Mock internal state to prevent side effects
    mocker.patch(
        "System.runtime.analyze_task",
        return_value=(True, "Approved", "FORGE", "STUDIO", {"total_tokens": 10}),
    )
    mocker.patch("System.organs.vestibular.commit_transaction")
    mocker.patch("System.organs.vestibular.restore_balance")

    # 2. Mock Agent to FAIL on the first try, but PASS on the retry
    call_count = {"qa_auditor": 0}

    def mock_run_agent_side_effect(*args, **kwargs):
        role_name = kwargs.get("role_name", args[0] if len(args) > 0 else "")
        if "Auditor" in role_name:
            call_count["qa_auditor"] += 1
            if call_count["qa_auditor"] == 1:
                # FIRST TRY: Explicitly trigger the retry using Broca's strict format
                return AgentResponse(text="<audit_result>FAIL</audit_result>", usage={})
            # RETRY: Explicitly pass using Broca's strict format
            return AgentResponse(text="<audit_result>PASS</audit_result>", usage={})
        return AgentResponse(text="Here is code.", usage={})

    mocker.patch("System.runtime.run_agent", side_effect=mock_run_agent_side_effect)

    # 3. Set Headless Flag (Shift-Left Input Bypass)
    mocker.patch.dict(os.environ, {"BRAIN_OS_HEADLESS": "1"})

    # 4. Aggressive crash if it accidentally asks for human input
    mocker.patch(
        "builtins.input", side_effect=Exception("Test failed: HITL prompt triggered!")
    )

    # 5. Execute
    execute_pipeline("Test retry", "FORGE", "STUDIO")

    # Assert it called the auditor twice (initial + retry) safely
    assert call_count["qa_auditor"] == 2
