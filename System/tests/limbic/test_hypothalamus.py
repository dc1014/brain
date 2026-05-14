import pytest
from System.neuroanatomy.limbic.hypothalamus import regulate_api_heartbeat


@pytest.mark.asyncio
async def test_hypothalamus_healthy_heartbeat():
    """Proves the Hypothalamus stays out of the way when the API is healthy."""

    async def mock_success():
        return "Success"

    result = await regulate_api_heartbeat(mock_success)
    assert result == "Success"


@pytest.mark.asyncio
async def test_hypothalamus_rate_limit_recovery(mocker):
    """Proves the Hypothalamus intercepts a 429, sleeps, and retries successfully."""
    # Mock sleep so our tests don't actually wait 2 seconds
    mocker.patch("System.neuroanatomy.limbic.hypothalamus.asyncio.sleep")

    attempts = 0

    async def mock_flaky_api():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise Exception("HTTP 429: Too Many Requests")
        return "Recovered"

    result = await regulate_api_heartbeat(mock_flaky_api)
    assert result == "Recovered"
    assert attempts == 2


@pytest.mark.asyncio
async def test_hypothalamus_cardiac_arrest(mocker):
    """Proves the system eventually fails if the rate limit never clears."""
    mocker.patch("System.neuroanatomy.limbic.hypothalamus.asyncio.sleep")

    async def mock_dead_api():
        raise Exception("Rate limit exceeded")

    with pytest.raises(Exception, match="HYPOTHALAMUS FAILURE"):
        await regulate_api_heartbeat(mock_dead_api)


@pytest.mark.asyncio
async def test_hypothalamus_passes_fatal_errors():
    """Proves the Hypothalamus doesn't retry bad auth or 500 errors."""

    async def mock_auth_error():
        raise ValueError("Invalid API Key")

    with pytest.raises(ValueError, match="Invalid API Key"):
        await regulate_api_heartbeat(mock_auth_error)
