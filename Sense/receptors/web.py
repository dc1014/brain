# --- Sense/receptors/web.py ---
import socket
import ipaddress
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from markdownify import markdownify  # type: ignore

MAX_SENSORY_CHARS = 25000


class SecurityBlockError(Exception):
    pass


class TargetValidator:
    @staticmethod
    def validate_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            raise SecurityBlockError("Only HTTP/HTTPS stimuli are allowed.")
        try:
            hostname = parsed.hostname
            if not hostname:
                raise SecurityBlockError("Invalid URL: No hostname provided.")
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip_str == "0.0.0.0":
                raise SecurityBlockError(
                    f"SSRF BLOCK: Attempted to access restricted subnet ({ip_str})."
                )
        except socket.gaierror:
            raise SecurityBlockError(
                f"DNS RESOLUTION FAILED: Could not resolve {parsed.hostname}"
            )
        except ValueError:
            raise SecurityBlockError(f"INVALID IP ADDRESS: {ip_str}")
        return url


def transduce_web_page(url: str) -> str:
    try:
        safe_url = TargetValidator.validate_url(url)
    except SecurityBlockError as e:
        return f'<sensory_error source="{url}">\n{str(e)}\n</sensory_error>'

    # Lazy import prevents CI/CD and clean setup failures
    try:
        from playwright.sync_api import (
            sync_playwright,
            TimeoutError as PlaywrightTimeoutError,
        )
    except ImportError:
        return f'<sensory_error source="{url}">\nVision extras not installed. Run "ctx setup" and enable the Retina sense.\n</sensory_error>'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CoreTexOS/1.0"
        )
        page = context.new_page()

        page.route(
            "**/*",
            lambda route: (
                route.abort()
                if route.request.resource_type
                in ["image", "media", "font", "stylesheet"]
                else route.continue_()
            ),
        )

        try:
            page.goto(safe_url, timeout=15000, wait_until="networkidle")
            html_content = page.content()
        except PlaywrightTimeoutError:
            html_content = page.content()
        finally:
            browser.close()

    soup = BeautifulSoup(html_content, "html.parser")

    for element in soup(
        [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "noscript",
            "iframe",
            "svg",
        ]
    ):
        element.decompose()

    markdown_content = markdownify(str(soup), heading_style="ATX").strip()

    if not markdown_content:
        return "Page rendered successfully but contained no extractable text."

    if len(markdown_content) > MAX_SENSORY_CHARS:
        markdown_content = (
            markdown_content[:MAX_SENSORY_CHARS]
            + "\n\n... [TRUNCATED BY CORETEX OS TO PREVENT TOKEN EXHAUSTION] ..."
        )

    return markdown_content
