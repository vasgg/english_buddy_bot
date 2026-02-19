from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sqlite3
import sys
import time
from collections.abc import Iterable
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.append(str(SRC))

from sqlalchemy import insert, text as sa_text  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from database.models.base import Base  # noqa: E402
import database.tables_helper  # noqa: F401,E402

logger = logging.getLogger("migrate_sqlite_to_postgres")

TABLE_ORDER = [
    "lessons",
    "users",
    "texts",
    "reactions",
    "stickers",
    "reminder_text_variants",
    "notification_campaigns",
    "notification_segments",
    "sessions",
    "slides",
    "quiz_answer_logs",
    "notification_deliveries",
]

DATETIME_COLUMNS = {
    "created_at",
    "last_reminded_at",
    "last_activity_at",
    "last_lesson_completed_at",
    "last_notification_sent_at",
    "completed_at",
    "send_at",
    "registered_before",
    "registered_after",
    "last_activity_before",
    "last_activity_after",
    "last_lesson_completed_before",
    "last_lesson_completed_after",
    "last_notification_sent_before",
    "last_notification_sent_after",
    "scheduled_at",
    "sent_at",
}
DATE_COLUMNS = {"subscription_expired_at"}


DEFAULT_LOG_FILE = ROOT / "migrate_sqlite_to_postgres.log"


def _setup_logging(log_file: Path, level: str) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level!r}")

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03dZ [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    formatter.converter = time.gmtime  # timestamps in UTC

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(numeric_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)


def _redact_url(url: str) -> str:
    # Best-effort: replace password part of "user:pass@" with "user:***@".
    try:
        prefix, rest = url.split("://", 1)
    except ValueError:
        return "<invalid DATABASE_URL>"
    if "@" not in rest:
        return f"{prefix}://{rest}"
    creds, tail = rest.split("@", 1)
    if ":" not in creds:
        return f"{prefix}://{creds}@{tail}"
    user, _pw = creds.split(":", 1)
    return f"{prefix}://{user}:***@{tail}"


def _chunked(items: list[dict], chunk_size: int) -> Iterable[list[dict]]:
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


def _sqlite_rows(conn: sqlite3.Connection, table: str) -> list[dict]:
    try:
        if table == "quiz_answer_logs":
            # SQLite might contain orphaned logs (foreign keys are often disabled),
            # but Postgres enforces FKs. Filter those out on read.
            total = conn.execute("SELECT COUNT(*) FROM quiz_answer_logs").fetchone()[0]
            cursor = conn.execute(
                """
                SELECT qal.*
                FROM quiz_answer_logs AS qal
                JOIN sessions AS s ON s.id = qal.session_id
                JOIN slides AS sl ON sl.id = qal.slide_id
                """
            )
        else:
            cursor = conn.execute(f"SELECT * FROM {table}")
    except sqlite3.OperationalError:
        return []
    rows = [dict(row) for row in cursor.fetchall()]
    if table == "quiz_answer_logs":
        dropped = int(total) - len(rows)
        if dropped:
            logger.warning("Dropped %s orphan quiz_answer_logs rows during SQLite read", dropped)
    return rows


def _prepare_users(rows: list[dict]) -> list[dict]:
    for row in rows:
        row.setdefault("last_activity_at", None)
        row.setdefault("last_lesson_completed_at", None)
        row.setdefault("last_notification_sent_at", None)
        row.setdefault("notifications_enabled", 1)
        row.setdefault("completed_lessons_count", 0)
        row.setdefault("completed_all_lessons", 0)
    return rows


def _prepare_sessions(rows: list[dict]) -> list[dict]:
    for row in rows:
        if "completed_at" not in row:
            status = row.get("status")
            if status == "COMPLETED":
                row["completed_at"] = row.get("created_at")
            else:
                row["completed_at"] = None
    return rows


def _normalize_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return value


def _normalize_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


def _filter_columns(table, rows: list[dict]) -> list[dict]:
    columns = set(table.c.keys())
    filtered = []
    for row in rows:
        normalized = {}
        for key, value in row.items():
            if key not in columns:
                continue
            if key in DATETIME_COLUMNS:
                value = _normalize_datetime(value)
            if key in DATE_COLUMNS:
                value = _normalize_date(value)
            normalized[key] = value
        filtered.append(normalized)
    return filtered


async def _insert_rows(session_maker, table, rows: list[dict], *, chunk_size: int) -> None:
    if not rows:
        return
    async with session_maker() as session:
        for n, chunk in enumerate(_chunked(rows, chunk_size), start=1):
            try:
                # Use executemany-style call; it's easier to debug by chunk.
                await session.execute(insert(table), chunk)
                await session.commit()
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                logger.exception(
                    "Failed inserting into %s (chunk %s, rows %s..%s): %s",
                    table.name,
                    n,
                    (n - 1) * chunk_size + 1,
                    (n - 1) * chunk_size + len(chunk),
                    exc,
                )
                raise


async def _reset_sequences(session_maker, table_names: list[str]) -> None:
    async with session_maker() as session:
        for table in table_names:
            stmt = sa_text(
                """
                SELECT
                    CASE
                        WHEN pg_get_serial_sequence(:table_name, 'id') IS NULL THEN NULL
                        ELSE setval(
                            pg_get_serial_sequence(:table_name, 'id'),
                            COALESCE((SELECT MAX(id) FROM {table}), 1),
                            (SELECT MAX(id) FROM {table}) IS NOT NULL
                        )
                    END;
                """.format(table=table)
            )
            await session.execute(stmt, {"table_name": table})
        await session.commit()


async def migrate(sqlite_path: Path, database_url: str, *, chunk_size: int, sql_echo: bool) -> None:
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row

    engine = create_async_engine(
        database_url,
        echo=sql_echo,
        connect_args={"server_settings": {"timezone": "UTC"}},
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    for table_name in TABLE_ORDER:
        if table_name not in Base.metadata.tables:
            continue
        logger.info("Migrating table: %s", table_name)
        rows = _sqlite_rows(conn, table_name)
        logger.info("SQLite rows fetched: %s", len(rows))
        if table_name == "users":
            rows = _prepare_users(rows)
        if table_name == "sessions":
            rows = _prepare_sessions(rows)
        rows = _filter_columns(Base.metadata.tables[table_name], rows)
        logger.info("Rows after column filter/normalization: %s", len(rows))
        await _insert_rows(session_maker, Base.metadata.tables[table_name], rows, chunk_size=chunk_size)

    await _reset_sequences(session_maker, [t for t in TABLE_ORDER if t in Base.metadata.tables])
    await engine.dispose()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite-path", default="prod_english_buddy.db")
    parser.add_argument("--log-file", default=str(DEFAULT_LOG_FILE))
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--sql-echo", action="store_true")
    args = parser.parse_args()

    _setup_logging(Path(args.log_file), args.log_level)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for migration")
    logger.info("DATABASE_URL=%s", _redact_url(database_url))

    sqlite_path = Path(args.sqlite_path)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {sqlite_path}")

    logger.info("SQLite path: %s", sqlite_path)
    logger.info("Log file: %s", args.log_file)
    logger.info("Chunk size: %s", args.chunk_size)
    logger.info("SQL echo: %s", args.sql_echo)

    try:
        asyncio.run(
            migrate(
                sqlite_path,
                database_url,
                chunk_size=max(1, int(args.chunk_size)),
                sql_echo=bool(args.sql_echo),
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Migration failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
