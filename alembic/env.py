from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine.url import make_url

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.append(str(SRC))

from database.models.base import Base  # noqa: E402
import database.tables_helper  # noqa: F401,E402


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(override=False)


def get_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set for Alembic migrations")
    url_obj = make_url(url)
    if url_obj.drivername != "postgresql+asyncpg":
        raise RuntimeError(
            "DATABASE_URL must point to PostgreSQL with asyncpg driver, "
            "for example: postgresql+asyncpg://user:pass@host:5432/dbname"
        )
    return url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(
        get_url(),
        poolclass=pool.NullPool,
        pool_pre_ping=True,
        connect_args={"server_settings": {"timezone": "UTC"}},
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    _maybe_load_dotenv()
    run_migrations_offline()
else:
    _maybe_load_dotenv()
    asyncio.run(run_migrations_online())
