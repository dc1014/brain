from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_installs_deno_into_non_root_path() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert 'ENV DENO_INSTALL="/opt/deno"' in dockerfile
    assert 'ENV DENO_INSTALL="/root/.deno"' not in dockerfile
    assert "ln -s" in dockerfile
    assert 'ENV PATH="$DENO_INSTALL/bin:$PATH"' in dockerfile


def test_compose_preserves_deno_path_for_host_uid_runtime() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    coretex = compose["services"]["coretex"]

    assert "DENO_INSTALL=/opt/deno" in coretex["environment"]
    assert (
        "PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games"
        in coretex["environment"]
    )
