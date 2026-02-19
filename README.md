# Telegram-bot for learning english.

[![CI](https://github.com/vasgg/english_buddy_bot/actions/workflows/python-app.yml/badge.svg)](https://github.com/vasgg/english_buddy_bot/actions?query=branch%3Amain++)
-----

## Development

This project uses `uv` for dependency management.
Python version: `3.13` (see `.python-version`).

### Infrastructure
Postgres and Redis are expected to be provided by external infrastructure (separate compose).
This repository does **not** include a local `compose.yml`.

### Required environment variables
Set these in `.env` (see `.env.example`):
- `DATABASE_URL` (Postgres, asyncpg)
- `REDIS_URL`
- `TASKIQ_REDIS_URL`
- `BOT_TOKEN`
- `ADMIN`, `SUB_ADMINS`, `TEACHERS`
- `TOP_BAD_SLIDES_COUNT`
- `STAGE`
- Optional: `SENTRY_AIOGRAM_DSN`, `SENTRY_FASTAPI_DSN`

Example:
```
DATABASE_URL=postgresql+asyncpg://user:pass@127.0.0.1:5432/english_buddy_bot
REDIS_URL=redis://:redis_pass@127.0.0.1:6379/1
TASKIQ_REDIS_URL=redis://:redis_pass@127.0.0.1:6379/2
```

### Setup & checks
- Install dependencies: `uv sync --all-groups`
- Run tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Format check: `uv run ruff format --check .`
- Typecheck (informational): `uv run ty check src`

### Database migrations
- Run migrations: `DATABASE_URL=... uv run alembic upgrade head`
- Create new migration: `DATABASE_URL=... uv run alembic revision --autogenerate -m "message"`

### Data migration (SQLite -> Postgres)
If you have an existing SQLite DB file:
- `DATABASE_URL=... uv run python scripts/migrate_sqlite_to_postgres.py --sqlite-path prod_english_buddy.db`

### Run
- Run bot (polling): `uv run bot-run` (requires Redis)
- Run webapp: `uv run webapp-run`

### Background Workers (Taskiq)
This project uses Taskiq for background jobs (notifications, daily routine).
Make sure you run **both** worker and scheduler in production.

Run worker (start with 1 process, increase later if needed):
```bash
uv run --env-file .env worker-run --workers 1
```

Run scheduler:
```bash
uv run --env-file .env scheduler-run --skip-first-run
```
