import aiohttp
import os
from System.core.onboarding.security import is_valid_key_format


async def scan_ollama() -> bool:
    """Pings the default local Ollama port to see if a local engine is active."""
    try:
        # SHIFT-LEFT: Strictly type the timeout object for aiohttp
        timeout = aiohttp.ClientTimeout(total=2.0)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:11434/api/tags", timeout=timeout
            ) as resp:
                return resp.status == 200
    except Exception:
        return False


async def verify_api_key(provider: str, api_key: str, model: str) -> bool:
    """
    Two-stage verification:
    1. Validates the raw string regex to prevent unnecessary network calls.
    2. Fires a 1-token LLM ping to verify active billing and quota.
    """
    api_key = api_key.strip()
    if not api_key:
        return False

    # Stage 1: Shift-Left Regex Gate
    if not is_valid_key_format(provider, api_key):
        return False

    # Delay import to ensure environment isolation during boot
    from litellm import acompletion

    env_var_name = f"{provider.upper()}_API_KEY"
    original_key = os.environ.get(env_var_name)

    # Temporarily inject for litellm
    os.environ[env_var_name] = api_key

    try:
        # Stage 2: The 1-Token Ping
        await acompletion(
            model=model, messages=[{"role": "user", "content": "hi"}], max_tokens=1
        )
        return True
    except Exception:
        # Catches 401 Unauthorized, 429 Insufficient Quota, etc.
        return False
    finally:
        # STRICT CLEANUP: Never leak credentials in the active os.environ shell
        if original_key is not None:
            os.environ[env_var_name] = original_key
        else:
            del os.environ[env_var_name]
