from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_setup_ps1_exposes_parity_flags_and_check_output() -> None:
    setup = (ROOT / "setup.ps1").read_text(encoding="utf-8")

    assert "[switch]$Check" in setup
    assert "[switch]$Docker" in setup
    assert "[switch]$Local" in setup
    assert "[switch]$Help" in setup
    assert "docker_engine:" in setup
    assert "docker_compose:" in setup
    assert "Choose either -Docker or -Local" in setup


def test_setup_ps1_can_install_missing_local_runtimes() -> None:
    setup = (ROOT / "setup.ps1").read_text(encoding="utf-8")

    assert "Install-UvRuntime" in setup
    assert "https://astral.sh/uv/install.ps1" in setup
    assert "Install-DenoRuntime" in setup
    assert "https://deno.land/install.ps1" in setup
    assert "uv installation failed or could not be found in PATH" in setup
    assert "deno installation failed or could not be found in PATH" in setup


def test_setup_ps1_docker_path_requires_compose_and_uses_wrapper() -> None:
    setup = (ROOT / "setup.ps1").read_text(encoding="utf-8")

    assert "Test-DockerComposeAvailable" in setup
    assert "Docker Compose is unavailable" in setup
    assert "Invoke-DockerCompose build" in setup
    assert ".\\ctx.bat --docker setup" in setup


def test_ctx_bat_docker_path_fails_fast_when_image_missing() -> None:
    ctx = (ROOT / "ctx.bat").read_text(encoding="utf-8")

    assert "docker image inspect coretex" in ctx
    assert "Docker runtime requested" in ctx
    assert ".\\setup.ps1 -Docker" in ctx
    assert "docker compose run --rm coretex" in ctx
