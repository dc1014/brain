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
        # 🛡️ THE FIX: Added "default-model" to the mocked user inputs
        side_effect=["1", "sk-or-1234", "default-model", "brave-key"],
    )
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=False)

    keys = await harvest_credentials()
    assert keys["OPENROUTER_API_KEY"] == "sk-or-1234"
    assert keys["__DEFAULT_MODEL__"] == "default-model"
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
        # 🛡️ THE FIX: Added "default-model" to the mocked user inputs
        side_effect=["2", "sk-oa", "sk-ant", "", "default-model", ""],
    )
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=False)

    keys = await harvest_credentials()
    assert keys["OPENAI_API_KEY"] == "sk-oa"
    assert keys["ANTHROPIC_API_KEY"] == "sk-ant"
    assert keys["__DEFAULT_MODEL__"] == "default-model"
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
        # 🛡️ THE FIX: Added "default-model" to the mocked user inputs
        side_effect=["3", "https://proxy", "proxy-key", "default-model", ""],
    )
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=False)

    keys = await harvest_credentials()
    assert keys["GATEWAY_BASE_URL"] == "https://proxy"
    assert keys["GATEWAY_API_KEY"] == "proxy-key"
    assert keys["__DEFAULT_MODEL__"] == "default-model"
    assert keys["USE_LOCAL_SLM"] == "false"


@pytest.mark.asyncio
async def test_harvest_credentials_skip_local_only(mocker):
    """Proves the local-only path gracefully skips cloud LLM keys for air-gapped execution."""
    mocker.patch(
        "System.core.onboarding.genesis.urllib.request.urlopen", side_effect=Exception
    )
    # 🛡️ THE FIX: Added "default-model" to the mocked user inputs
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=["4", "default-model", ""],
    )
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=False)

    keys = await harvest_credentials()
    # Cloud keys must be empty, and since they said False to SLMs, USE_LOCAL_SLM is false
    assert "OPENAI_API_KEY" not in keys
    assert "OPENROUTER_API_KEY" not in keys
    assert keys["__DEFAULT_MODEL__"] == "default-model"
    assert keys["USE_LOCAL_SLM"] == "false"


@pytest.mark.asyncio
async def test_harvest_credentials_local_slm_discovery(mocker):
    """Proves the wizard successfully configures Corpus Callosum overrides for Local SLMs."""
    # Mock urllib to simulate Ollama successfully responding to the probe
    mocker.patch("System.core.onboarding.genesis.urllib.request.urlopen")
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        # 🛡️ THE FIX: Added "default-model" to the mocked user inputs
        side_effect=["4", "default-model", "", "ollama/llama3.2"],
    )

    # Simulate user answering "Yes" to enabling the Local SLM
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=True)

    keys = await harvest_credentials()

    assert keys["USE_LOCAL_SLM"] == "true"
    assert keys["LOCAL_MODEL_NAME"] == "ollama/llama3.2"
    assert keys["__DEFAULT_MODEL__"] == "default-model"
    assert "OPENROUTER_API_KEY" not in keys


def test_bind_workspace_local(mocker, tmp_path):
    """Proves the local workspace builder constructs Obsidian domains and seeds memory ledgers."""
    mocker.patch("System.core.onboarding.genesis.IS_DOCKER_RUNTIME", False)

    mocker.patch("System.core.onboarding.genesis.ROOT_DIR", tmp_path)

    mocker.patch("System.core.onboarding.genesis.Prompt.ask", return_value="")
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=False)

    path_str = bind_workspace()
    expected_path = tmp_path

    # Verify Unified Root Pathing
    assert path_str == str(expected_path)

    # Verify Domain Folder Creation
    assert (expected_path / "Studio").exists()
    assert (expected_path / "Meta").exists()
    assert (expected_path / "Media").exists()

    personal_ledger = expected_path / "Personal" / "personal-memory.md"
    assert personal_ledger.exists()

    content = personal_ledger.read_text(encoding="utf-8")
    assert "# Personal Context" in content
    assert "Synaptic Ledger initialized" in content

    # Verify custom mapping for Meta
    meta_ledger = expected_path / "Meta" / "global-memory.md"
    assert meta_ledger.exists()
    assert "# Meta Context" in meta_ledger.read_text(encoding="utf-8")

    # Prove Media correctly skips ledger creation
    media_ledger_matches = list((expected_path / "Media").glob("*.md"))
    assert len(media_ledger_matches) == 0, (
        "Media folder should not contain a text ledger"
    )


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
