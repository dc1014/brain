import pytest
from Sense.receptors.web import transduce_web_page, TargetValidator, SecurityBlockError


def test_target_validator_blocks_ssrf():
    """Proves the TargetValidator intercepts local network and private IP addresses."""

    with pytest.raises(SecurityBlockError) as exc:
        TargetValidator.validate_url("http://127.0.0.1/admin")
    assert "SSRF BLOCK" in str(exc.value)

    with pytest.raises(SecurityBlockError) as exc:
        TargetValidator.validate_url("http://localhost:8080")
    assert "SSRF BLOCK" in str(exc.value)

    with pytest.raises(SecurityBlockError) as exc:
        TargetValidator.validate_url("file:///etc/passwd")
    assert "Only HTTP/HTTPS" in str(exc.value)


def test_transduce_web_page_success(mocker):
    """Proves the Playwright receptor correctly renders and strips HTML noise."""
    pytest.importorskip("playwright")

    mocker.patch("socket.gethostbyname", return_value="8.8.8.8")

    mock_sync_playwright = mocker.patch("playwright.sync_api.sync_playwright")

    mock_context_manager = mocker.MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_context_manager

    mock_browser = mocker.MagicMock()
    mock_context_manager.chromium.launch.return_value = mock_browser

    mock_context = mocker.MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_page = mocker.MagicMock()
    mock_context.new_page.return_value = mock_page

    mock_page.content.return_value = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <header>Ignore this</header>
            <h1>Main Content</h1>
            <p>This is the core text.</p>
            <script>alert('bad');</script>
        </body>
    </html>
    """

    result = transduce_web_page("https://example.com")

    assert "Main Content" in result
    assert "This is the core text." in result
    assert "Ignore this" not in result
    assert "alert('bad')" not in result


def test_transduce_web_page_token_guillotine(mocker):
    """Proves the receptor truncates massive pages to protect the LLM token budget."""
    pytest.importorskip("playwright")

    mocker.patch("socket.gethostbyname", return_value="8.8.8.8")

    mock_sync_playwright = mocker.patch("playwright.sync_api.sync_playwright")

    mock_context_manager = mocker.MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_context_manager

    mock_browser = mocker.MagicMock()
    mock_context_manager.chromium.launch.return_value = mock_browser

    mock_context = mocker.MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_page = mocker.MagicMock()
    mock_context.new_page.return_value = mock_page

    massive_content = "<p>" + ("Word " * 10000) + "</p>"
    mock_page.content.return_value = f"<html><body>{massive_content}</body></html>"

    result = transduce_web_page("https://example.com")

    assert len(result) < 30000
    assert "[TRUNCATED BY CORETEX OS TO PREVENT TOKEN EXHAUSTION]" in result
