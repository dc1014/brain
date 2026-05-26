from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_script(*args: str, path: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if path is not None:
        env["PATH"] = path
    cmd = [str(ROOT / args[0]), *args[1:]]
    if os.name == "nt":
        git_bash = r"C:\Program Files\Git\bin\bash.exe"
        if os.path.exists(git_bash):
            cmd = [git_bash, *cmd]
        else:
            cmd = ["bash", *cmd]
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )


def test_setup_help_advertises_docker_and_local_flags() -> None:
    result = run_script("setup.sh", "--help")

    assert result.returncode == 0
    assert "--check" in result.stdout
    assert "--docker" in result.stdout
    assert "--local" in result.stdout


def test_setup_can_install_missing_local_runtimes() -> None:
    setup = (ROOT / "setup.sh").read_text(encoding="utf-8")

    assert "install_uv_runtime" in setup
    assert "https://astral.sh/uv/install.sh" in setup
    assert "install_deno_runtime" in setup
    assert "https://deno.land/install.sh" in setup
    assert "uv installation completed but uv was not found in PATH" in setup
    assert "Deno installation completed but deno was not found in PATH" in setup


def test_setup_rejects_mutually_exclusive_runtime_flags() -> None:
    result = run_script("setup.sh", "--docker", "--local")

    assert result.returncode == 2
    assert "choose either --docker or --local" in result.stdout


def test_setup_check_reports_docker_compose_status() -> None:
    result = run_script("setup.sh", "--check")

    assert "docker_engine:" in result.stdout
    assert "docker_compose:" in result.stdout


def test_ctx_docker_flag_fails_fast_when_image_is_not_built(tmp_path: Path) -> None:
    docker_bin = tmp_path / "docker"
    docker_bin.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$1" = "image" ] && [ "$2" = "inspect" ]; then exit 1; fi\n'
        "exit 0\n",
        encoding="utf-8",
    )
    docker_bin.chmod(0o755)

    result = run_script("ctx", "--docker", "status", path=str(tmp_path))

    assert result.returncode == 1
    assert "Docker runtime requested" in result.stdout
    assert "./setup.sh --docker" in result.stdout
