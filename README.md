# Telegram-bot for learning english.

[![CI](https://github.com/vasgg/english_buddy_bot/actions/workflows/python-app.yml/badge.svg)](https://github.com/vasgg/english_buddy_bot/actions?query=branch%3Amain++)
-----

## Development

This project uses `uv` for dependency management.
Python version: `3.13` (see `.python-version`).

- Install dependencies: `uv sync --all-groups`
- Run tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Typecheck (informational for now): `uv run ty check src`
- Run bot (polling): `uv run bot-run` (requires Redis, see `compose.yml`)
- Run webapp: `uv run webapp-run` (or `source .venv/bin/activate && webapp-run`)
