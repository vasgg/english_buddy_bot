from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.append(str(SRC))

from sqlalchemy import insert, text as sa_text  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from database.models.base import Base  # noqa: E402
import database.tables_helper  # noqa: F401,E402


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


def _sqlite_rows(conn: sqlite3.Connection, table: str) -> list[dict]:
    try:
        cursor = conn.execute(f"SELECT * FROM {table}")
    except sqlite3.OperationalError:
        return []
    rows = [dict(row) for row in cursor.fetchall()]
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


async def _insert_rows(session_maker, table, rows: list[dict]) -> None:
    if not rows:
        return
    async with session_maker() as session:
        await session.execute(insert(table).values(rows))
        await session.commit()


async def _reset_sequences(session_maker, table_names: list[str]) -> None:
    async with session_maker() as session:
        for table in table_names:
            stmt = sa_text(
                """
                SELECT setval(
                    pg_get_serial_sequence(:table_name, 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 1),
                    (SELECT MAX(id) FROM {table}) IS NOT NULL
                );
                """.format(table=table)
            )
            await session.execute(stmt, {"table_name": table})
        await session.commit()


async def migrate(sqlite_path: Path, database_url: str) -> None:
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row

    engine = create_async_engine(database_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    for table_name in TABLE_ORDER:
        if table_name not in Base.metadata.tables:
            continue
        rows = _sqlite_rows(conn, table_name)
        if table_name == "users":
            rows = _prepare_users(rows)
        if table_name == "sessions":
            rows = _prepare_sessions(rows)
        rows = _filter_columns(Base.metadata.tables[table_name], rows)
        await _insert_rows(session_maker, Base.metadata.tables[table_name], rows)

    await _reset_sequences(session_maker, [t for t in TABLE_ORDER if t in Base.metadata.tables])
    await engine.dispose()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite-path", default="prod_english_buddy.db")
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for migration")

    sqlite_path = Path(args.sqlite_path)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {sqlite_path}")

    asyncio.run(migrate(sqlite_path, database_url))


if __name__ == "__main__":
    main()
