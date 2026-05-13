import pytest
from receptors.web import TargetValidator, SecurityBlockError, transduce_web_page


def test_target_validator_ssrf_blocks(monkeypatch):
    """Proves that Sense blocks all SSRF vectors."""

    # 1. Mock DNS to return a loopback IP (127.0.0.1)
    monkeypatch.setattr("socket.gethostbyname", lambda x: "127.0.0.1")
    with pytest.raises(SecurityBlockError, match="SSRF BLOCK"):
        TargetValidator.validate_url("http://localhost:8000")

    # 2. Mock DNS to return an AWS Metadata IP (169.254.169.254)
    monkeypatch.setattr("socket.gethostbyname", lambda x: "169.254.169.254")
    with pytest.raises(SecurityBlockError, match="SSRF BLOCK"):
        TargetValidator.validate_url("http://aws-metadata-hack.com")

    # 3. Block non-HTTP protocols
    with pytest.raises(SecurityBlockError, match="Only HTTP/HTTPS"):
        TargetValidator.validate_url("file:///etc/passwd")


def test_transduce_web_page_success(monkeypatch):
    """Proves HTML is successfully transduced to Markdown Action Potentials."""

    # Mock DNS and HTTP
    monkeypatch.setattr("socket.gethostbyname", lambda x: "8.8.8.8")

    class MockResponse:
        text = (
            "<html><body><h1>Test Page</h1><script>ignore_me()</script></body></html>"
        )

        def raise_for_status(self):
            pass

    monkeypatch.setattr("httpx.Client.get", lambda *args, **kwargs: MockResponse())

    result = transduce_web_page("http://safe-site.com")

    assert "<sensory_input" in result
    assert "# Test Page" in result
    assert "ignore_me" not in result  # Proves the token-wasting script tag was stripped
