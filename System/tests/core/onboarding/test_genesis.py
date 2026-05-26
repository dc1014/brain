import pytest
from System.core.onboarding.genesis import harvest_credentials, bind_workspace


@pytest.mark.asyncio
async def test_harvest_credentials_openrouter(mocker):
    """Proves the setup wizard prioritizes and successfully maps OpenRouter."""
    mocker.patch(
        "System.core.onboarding.genesis.urllib.request.urlopen", side_effect=Exception
    )
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["1", "sk-or-1234", "brave-key"],
    )
    mocker.patch(
        "System.core.onboarding.genesis.Confirm.ask", return_value=False
    )  # ⚡ FIX: Mock boolean prompt

    keys = await harvest_credentials()
    assert keys["OPENROUTER_API_KEY"] == "sk-or-1234"
    assert keys["BRAVE_API_KEY"] == "brave-key"
    assert keys["USE_LOCAL_SLM"] == "false"


@pytest.mark.asyncio
async def test_harvest_credentials_raw(mocker):
    """Proves raw individual providers can still be explicitly registered."""
    mocker.patch(
        "System.core.onboarding.genesis.urllib.request.urlopen", side_effect=Exception
    )
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["2", "sk-oa", "sk-ant", "", ""],
    )
    mocker.patch(
        "System.core.onboarding.genesis.Confirm.ask", return_value=False
    )  # ⚡ FIX: Mock boolean prompt

    keys = await harvest_credentials()
    assert keys["OPENAI_API_KEY"] == "sk-oa"
    assert keys["ANTHROPIC_API_KEY"] == "sk-ant"
    assert "GEMINI_API_KEY" not in keys
    assert keys["USE_LOCAL_SLM"] == "false"


@pytest.mark.asyncio
async def test_harvest_credentials_gateway(mocker):
    """Proves custom Cloudflare/Portkey gateways are correctly assembled."""
    mocker.patch(
        "System.core.onboarding.genesis.urllib.request.urlopen", side_effect=Exception
    )
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["3", "https://proxy", "proxy-key", ""],
    )
    mocker.patch(
        "System.core.onboarding.genesis.Confirm.ask", return_value=False
    )  # ⚡ FIX: Mock boolean prompt

    keys = await harvest_credentials()
    assert keys["GATEWAY_BASE_URL"] == "https://proxy"
    assert keys["GATEWAY_API_KEY"] == "proxy-key"
    assert keys["USE_LOCAL_SLM"] == "false"


@pytest.mark.asyncio
async def test_harvest_credentials_skip_local_only(mocker):
    """Proves the local-only path gracefully skips cloud LLM keys for air-gapped execution."""
    mocker.patch(
        "System.core.onboarding.genesis.urllib.request.urlopen", side_effect=Exception
    )
    mocker.patch("System.core.onboarding.genesis.Prompt.ask", side_effect=["4", ""])
    mocker.patch(
        "System.core.onboarding.genesis.Confirm.ask", return_value=False
    )  # ⚡ FIX: Mock boolean prompt

    keys = await harvest_credentials()
    # Cloud keys must be empty, and since they said False to SLMs, USE_LOCAL_SLM is false
    assert "OPENAI_API_KEY" not in keys
    assert "OPENROUTER_API_KEY" not in keys
    assert keys["USE_LOCAL_SLM"] == "false"


@pytest.mark.asyncio
async def test_harvest_credentials_local_slm_discovery(mocker):
    """Proves the wizard successfully configures Corpus Callosum overrides for Local SLMs."""
    # Mock urllib to simulate Ollama successfully responding to the probe
    mocker.patch("System.core.onboarding.genesis.urllib.request.urlopen")
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["4", "", "ollama/llama3.2"],
    )

    # ⚡ FIX: Simulate user answering "Yes" to enabling the Local SLM
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=True)

    keys = await harvest_credentials()

    assert keys["USE_LOCAL_SLM"] == "true"
    assert keys["LOCAL_MODEL_NAME"] == "ollama/llama3.2"
    assert "OPENROUTER_API_KEY" not in keys


def test_bind_workspace_local(mocker, tmp_path):
    """Proves the local workspace builder constructs Obsidian domains properly."""
    mocker.patch("System.core.onboarding.genesis.IS_DOCKER_RUNTIME", False)
    mocker.patch("System.core.onboarding.genesis.Path.home", return_value=tmp_path)
    mocker.patch("System.core.onboarding.genesis.Prompt.ask", return_value="")
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=False)

    path_str = bind_workspace()

    expected_path = tmp_path / "CoreTex"
    assert path_str == str(expected_path)
    assert (expected_path / "Studio").exists()
    assert (expected_path / "Meta").exists()


def test_bind_workspace_docker_override(mocker):
    """Proves Docker environments bypass user prompts and hard-lock the vault to /workspace."""
    mocker.patch("System.core.onboarding.genesis.IS_DOCKER_RUNTIME", True)
    mock_mkdir = mocker.patch("System.core.onboarding.genesis.Path.mkdir")
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=Exception("Prompt should be bypassed in Docker!"),
    )

    path_str = bind_workspace()
    assert path_str == "/workspace"
    assert mock_mkdir.called
