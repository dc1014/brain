import pytest
from unittest.mock import MagicMock
from Sense.receptors.web import transduce_web_page, TargetValidator, SecurityBlockError


def test_target_validator_blocks_ssrf():
    """Proves the receptor filters local subnets and loopbacks before connecting."""
    with pytest.raises(SecurityBlockError) as exc:
        TargetValidator.validate_url("http://localhost:8000")
    assert "SSRF BLOCK" in str(exc.value)

    with pytest.raises(SecurityBlockError) as exc:
        TargetValidator.validate_url("http://127.0.0.1/admin")
    assert "SSRF BLOCK" in str(exc.value)


def test_transduce_web_page_success(mocker):
    """Proves the Playwright receptor correctly renders and strips HTML noise."""

    # 1. Bypass SSRF DNS lookups in the test environment
    mocker.patch("socket.gethostbyname", return_value="8.8.8.8")

    # 2. ⚡ SHIFT-LEFT: Deep Mock of the Playwright Context Manager
    mock_sync_playwright = mocker.patch("Sense.receptors.web.sync_playwright")

    # Setup the nested mock chain: p.chromium.launch().new_context().new_page()
    mock_context_manager = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_context_manager

    mock_browser = MagicMock()
    mock_context_manager.chromium.launch.return_value = mock_browser

    mock_context = MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page

    # Inject our fake DOM containing noise tags
    fake_html = """
    <html>
        <body>
            <nav>Ignore this navigation menu</nav>
            <h1>Test Title</h1>
            <p>Main content area.</p>
            <script>alert("Malicious code");</script>
        </body>
    </html>
    """
    mock_page.content.return_value = fake_html

    # 3. Trigger sensory receptor
    result = transduce_web_page("https://safe-external-site.com")

    # 4. Assert Data Contracts & Cleaning
    assert "SUCCESS" in result
    assert "# Test Title" in result
    assert "Main content area." in result
    assert "Ignore this navigation menu" not in result
    assert "Malicious code" not in result


def test_transduce_web_page_token_guillotine(mocker):
    """Proves the receptor truncates massive pages to protect the LLM token budget."""
    mocker.patch("socket.gethostbyname", return_value="8.8.8.8")

    mock_sync_playwright = mocker.patch("Sense.receptors.web.sync_playwright")
    mock_context_manager = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_context_manager
    mock_browser = MagicMock()
    mock_context_manager.chromium.launch.return_value = mock_browser
    mock_context = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page

    # Generate an artificially massive HTML payload (30,000 characters)
    massive_text = "A" * 30000
    fake_html = f"<html><body><p>{massive_text}</p></body></html>"
    mock_page.content.return_value = fake_html

    result = transduce_web_page("https://massive-site.com")

    # Assert it was truncated
    assert len(result) < 30000
    assert "[TRUNCATED BY BRAIN OS TO PREVENT TOKEN EXHAUSTION]" in result
