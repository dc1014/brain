from pathlib import Path
from System.core.onboarding.path_binding import bind_global_alias


def test_bind_global_alias_linux_zsh(mocker, tmp_path: Path):
    """Proves the script correctly identifies zsh and formats the bash-style alias."""
    mocker.patch(
        "System.core.onboarding.path_binding.platform.system", return_value="Linux"
    )
    mocker.patch("System.core.onboarding.path_binding.Path.home", return_value=tmp_path)
    mocker.patch.dict("os.environ", {"SHELL": "/bin/zsh"})

    assert bind_global_alias()

    zshrc = tmp_path / ".zshrc"
    assert zshrc.exists()

    file_content = zshrc.read_text(encoding="utf-8")
    assert 'alias ctx="' in file_content
    assert "-m System.cli" in file_content


def test_bind_global_alias_windows_powershell(mocker, tmp_path: Path):
    """Proves the script routes Windows users to the .ps1 profile and uses a function wrapper."""
    mocker.patch(
        "System.core.onboarding.path_binding.platform.system", return_value="Windows"
    )
    mocker.patch("System.core.onboarding.path_binding.Path.home", return_value=tmp_path)

    assert bind_global_alias()

    ps_profile = (
        tmp_path
        / "Documents"
        / "WindowsPowerShell"
        / "Microsoft.PowerShell_profile.ps1"
    )
    assert ps_profile.exists()
    assert "function ctx {" in ps_profile.read_text(encoding="utf-8")


def test_bind_global_alias_idempotency(mocker, tmp_path: Path):
    """ZERO-DEBT: Proves the script will not duplicate the alias if the user runs setup twice."""
    mocker.patch(
        "System.core.onboarding.path_binding.platform.system", return_value="Linux"
    )
    mocker.patch("System.core.onboarding.path_binding.Path.home", return_value=tmp_path)
    mocker.patch.dict("os.environ", {"SHELL": "/bin/bash"})

    # Pre-populate the mock bashrc with an existing alias
    bashrc = tmp_path / ".bashrc"
    bashrc.write_text('alias ctx="cd /fake/path"\n', encoding="utf-8")

    # Mock the atomic writer so we can assert it is NEVER called
    mock_write = mocker.patch("System.core.onboarding.path_binding._atomic_write_text")

    assert bind_global_alias()
    mock_write.assert_not_called()
