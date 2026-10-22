"""Shared pytest setup.

SQLite does not enforce foreign keys by default, which hides insert-ordering
bugs that PostgreSQL rejects. Enable enforcement for the test engine so local
SQLite runs catch the same portability problems.
"""

from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./carepath-test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-characters")

from sqlalchemy import event  # noqa: E402

from carepath.db import engine  # noqa: E402


def _enable_sqlite_foreign_keys(dbapi_connection, _record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


if not event.contains(engine.sync_engine, "connect", _enable_sqlite_foreign_keys):
    event.listen(engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
