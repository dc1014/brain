uv run System/router.py logs --limit 2

uv run pytest System/tests

pre-commit run --all-files

uv run System/router.py task

uv run System/router.py sleep --synaptic