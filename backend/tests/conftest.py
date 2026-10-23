"""Shared pytest setup.

SQLite does not enforce foreign keys by default, which hides insert-ordering
bugs that PostgreSQL rejects. Enable enforcement for the test engine, force an
isolated test database (an ambient DATABASE_URL must not leak in), and provide
the shared API client fixture.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = os.environ.get(
    "CAREPATH_TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./carepath-test.db",
)
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-characters"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import event  # noqa: E402

from carepath.db import engine  # noqa: E402


def _sqlite_path() -> Path | None:
    if engine.url.get_backend_name() != "sqlite":
        return None
    database = engine.url.database
    return Path(database) if database else None


def _enable_sqlite_foreign_keys(dbapi_connection, _record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


if not event.contains(engine.sync_engine, "connect", _enable_sqlite_foreign_keys):
    event.listen(engine.sync_engine, "connect", _enable_sqlite_foreign_keys)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from carepath.db import Base
    from carepath.db import engine as app_engine
    from carepath.main import app
    from carepath.seed import seed_database

    await app_engine.dispose()
    db_path = _sqlite_path()
    if db_path and db_path.exists():
        db_path.unlink()
    async with app_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await seed_database()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    await app_engine.dispose()
    if db_path and db_path.exists():
        db_path.unlink()
