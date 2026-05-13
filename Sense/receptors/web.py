import socket
import ipaddress
import httpx
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from markdownify import markdownify  # type: ignore


class SecurityBlockError(Exception):
    """Raised when a sensory target violates Shift-Left security boundaries."""

    pass


class TargetValidator:
    """Biological Filter: Prevents SSRF attacks by strictly validating DNS resolution."""

    @staticmethod
    def validate_url(url: str) -> str:
        parsed = urlparse(url)

        # 1. Check protocol first
        if parsed.scheme not in ["http", "https"]:
            raise SecurityBlockError("Only HTTP/HTTPS stimuli are allowed.")

        # 2. Then check hostname
        hostname = parsed.hostname
        if not hostname:
            raise SecurityBlockError(f"Invalid URL structure: {url}")

        try:
            # 1. Resolve the hostname to an IP
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
        except socket.gaierror:
            raise SecurityBlockError(f"Could not resolve hostname: {hostname}")

        # 2. SHIFT-LEFT: Block local, private, loopback, and reserved IPs
        if (
            ip_obj.is_loopback
            or ip_obj.is_private
            or ip_obj.is_multicast
            or ip_obj.is_reserved
        ):
            raise SecurityBlockError(
                f"SSRF BLOCK: Attempted to access restricted subnet ({ip_str})."
            )

        return url


def transduce_web_page(url: str) -> str:
    """
    Acts as the biological receptor:
    1. Validates the safety of the stimulus (SSRF block).
    2. Fetches the raw HTML.
    3. Transduces HTML into clean, token-efficient Markdown.
    """
    try:
        safe_url = TargetValidator.validate_url(url)

        # Fast, modern HTTP fetch with strict timeouts
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(safe_url)
            response.raise_for_status()

        # Parse and strip noise
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove massive token-wasting tags
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Transduce to Markdown
        markdown_content = markdownify(str(soup), heading_style="ATX").strip()

        # Return the biological Action Potential (XML wrapped)
        return f'<sensory_input source="{safe_url}" status="SUCCESS">\n{markdown_content}\n</sensory_input>'

    except SecurityBlockError as e:
        return f'<sensory_error source="{url}" type="SECURITY_BLOCK">\n{str(e)}\n</sensory_error>'
    except Exception as e:
        return f'<sensory_error source="{url}" type="FETCH_FAILURE">\n{str(e)}\n</sensory_error>'
