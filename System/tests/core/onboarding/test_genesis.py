import pytest
from System.core.onboarding.genesis import harvest_credentials, bind_workspace


@pytest.mark.asyncio
async def test_harvest_credentials_openrouter(mocker):
    """Proves the setup wizard prioritizes and successfully maps OpenRouter."""
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["1", "sk-or-1234", "brave-key"],
    )
    keys = await harvest_credentials()
    assert keys["OPENROUTER_API_KEY"] == "sk-or-1234"
    assert keys["BRAVE_API_KEY"] == "brave-key"


@pytest.mark.asyncio
async def test_harvest_credentials_raw(mocker):
    """Proves raw individual providers can still be explicitly registered."""
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["2", "sk-oa", "sk-ant", "", ""],
    )
    keys = await harvest_credentials()
    assert keys["OPENAI_API_KEY"] == "sk-oa"
    assert keys["ANTHROPIC_API_KEY"] == "sk-ant"
    assert "GEMINI_API_KEY" not in keys


@pytest.mark.asyncio
async def test_harvest_credentials_gateway(mocker):
    """Proves custom Cloudflare/Portkey gateways are correctly assembled."""
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["3", "https://proxy", "proxy-key", ""],
    )
    keys = await harvest_credentials()
    assert keys["GATEWAY_BASE_URL"] == "https://proxy"
    assert keys["GATEWAY_API_KEY"] == "proxy-key"


def test_bind_workspace_local(mocker, tmp_path):
    """Proves the local workspace builder constructs Obsidian domains properly."""
    mocker.patch("System.core.onboarding.genesis.IS_DOCKER_RUNTIME", False)
    mocker.patch("System.core.onboarding.genesis.Path.home", return_value=tmp_path)

    # Simulate a user hitting Enter to accept the default vault path
    mocker.patch("System.core.onboarding.genesis.Prompt.ask", return_value="")

    # Simulate declining to auto-open the folder to avoid shell side-effects in CI
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=False)

    path_str = bind_workspace()

    expected_path = tmp_path / "CoreTex_Workspace"
    assert path_str == str(expected_path)

    # Assert structural integrity for Obsidian compliance
    assert (expected_path / "Studio").exists()
    assert (expected_path / "Meta").exists()


@pytest.mark.asyncio
async def test_harvest_credentials_skip_local_only(mocker):
    """Proves the local-only path gracefully skips cloud LLM keys for air-gapped execution."""
    from System.core.onboarding.genesis import harvest_credentials

    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["4", ""],  # '4' = Skip/Local LLMs, '' = Skip Brave key
    )
    keys = await harvest_credentials()

    # Assert the dictionary is completely empty (no cloud keys leaked or required)
    assert keys == {}


def test_bind_workspace_docker_override(mocker):
    """Proves Docker environments bypass user prompts and hard-lock the vault to /workspace."""
    from System.core.onboarding.genesis import bind_workspace

    mocker.patch("System.core.onboarding.genesis.IS_DOCKER_RUNTIME", True)

    # Mock mkdir to prevent actual file system modifications during the test
    mock_mkdir = mocker.patch("System.core.onboarding.genesis.Path.mkdir")

    # If the system attempts to prompt the user, the test will fail
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=Exception("Prompt should be bypassed in Docker!"),
    )

    path_str = bind_workspace()

    # Assert structural integrity and override compliance
    assert path_str == "/workspace"
    assert mock_mkdir.called
