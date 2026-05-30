import pytest
from System.core.onboarding.genesis import harvest_credentials, bind_workspace, main


@pytest.mark.asyncio
async def test_harvest_credentials_openrouter(mocker):
    """Proves the setup wizard prioritizes and successfully maps OpenRouter."""
    # ⚡ FIX: Mock the new async scan_ollama function instead of the legacy urllib
    mocker.patch("System.core.onboarding.genesis.scan_ollama", return_value=False)
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
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
    mocker.patch("System.core.onboarding.genesis.scan_ollama", return_value=False)
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=[
            "2",
            "openai-key",
            "anthropic-key",
            "gemini-key",
            "default-model",
            "brave-key",
        ],
    )
    mocker.patch("System.core.onboarding.genesis.Confirm.ask", return_value=False)

    keys = await harvest_credentials()
    assert keys["OPENAI_API_KEY"] == "openai-key"
    assert keys["ANTHROPIC_API_KEY"] == "anthropic-key"
    assert keys["GEMINI_API_KEY"] == "gemini-key"


def test_bind_workspace_expands_user_home(mocker, tmp_path):
    """Proves that a user typing '~/Vault' expands to their actual home directory safely."""
    mocker.patch("System.core.onboarding.genesis.IS_DOCKER_RUNTIME", False)
    mocker.patch("System.core.onboarding.genesis.is_headless_setup", return_value=False)

    # Simulate user typing ~/TestVault
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask", return_value="~/TestVault"
    )
    mocker.patch(
        "System.core.onboarding.genesis.Confirm.ask", return_value=False
    )  # Don't try to open OS window

    result_path = bind_workspace()

    # The literal ~ should not be in the output; it should be expanded to the physical home drive
    assert "~" not in result_path
    assert "TestVault" in result_path


@pytest.mark.asyncio
async def test_main_serializes_env_with_quotes(mocker, tmp_path):
    """Proves the main generator correctly wraps variables in double-quotes to prevent parsing crashes."""
    mocker.patch("System.core.onboarding.genesis.IS_DOCKER_RUNTIME", False)
    mocker.patch("System.core.onboarding.genesis.is_headless_setup", return_value=True)
    mocker.patch(
        "System.core.onboarding.genesis.verify_deno_sandbox", return_value=True
    )

    # Mock harvest_credentials to return a fake key
    mocker.patch(
        "System.core.onboarding.genesis.harvest_credentials",
        return_value={"TEST_KEY": "my fake key"},
    )

    # Force bind_workspace to return a path with spaces
    fake_workspace = tmp_path / "My Documents" / "Brain Vault"
    mocker.patch(
        "System.core.onboarding.genesis.bind_workspace",
        return_value=str(fake_workspace),
    )

    # Capture what gets written to the .env file
    mock_write = mocker.patch("System.core.onboarding.genesis._atomic_write_text")

    await main()

    # Find the call that wrote to the ENV_PATH
    env_write_call = next(
        (
            call
            for call in mock_write.call_args_list
            if str(call[0][0]).endswith(".env")
        ),
        None,
    )
    assert env_write_call is not None, ".env file was not written"

    env_content = env_write_call[0][1]

    # Verify the values are wrapped in double quotes
    assert f'CORETEX_VAULT_PATH="{fake_workspace}"' in env_content
    assert 'TEST_KEY="my fake key"' in env_content


def test_bind_workspace_docker_override(mocker):
    """Proves Docker environments bypass user prompts and hard-lock the vault to /workspace."""
    mocker.patch("System.core.onboarding.genesis.IS_DOCKER_RUNTIME", True)
    mock_mkdir = mocker.patch("System.core.onboarding.genesis.Path.mkdir")
    mocker.patch(
        "System.core.onboarding.genesis.Prompt.ask",
        side_effect=Exception("Prompt should be bypassed in Docker"),
    )

    path_str = bind_workspace()
    assert path_str == "/workspace"
    mock_mkdir.assert_called()
