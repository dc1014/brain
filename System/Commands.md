uv run System/cli.py logs --limit 2

uv run pytest System/tests

pre-commit run --all-files

uv run System/cli.py task

uv run System/cli.py sleep --synaptic