"""PostgreSQL smoke test.

Runs against a real PostgreSQL database: empty-schema migration, demo seed,
login, patient task completion, government aggregation and official dataset
import conflict. Exits 0 with SKIP when no PostgreSQL URL is configured.

Usage:
    CAREPATH_SMOKE_DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db \
        python scripts/postgres_smoke.py

The target schema is dropped and re-created, so never point this at a database
holding real data.
"""

from __future__ import annotations

import asyncio
import os
import sys


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def _ok(message: str) -> None:
    print(f"PASS: {message}")


def _configure_environment() -> str:
    url = os.environ.get("CAREPATH_SMOKE_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
    if not url.startswith("postgresql"):
        return ""
    os.environ["DATABASE_URL"] = url
    os.environ["APP_ENV"] = "test"
    os.environ.setdefault("SECRET_KEY", "postgres-smoke-secret-key-at-least-32-chars")
    return url


async def _reset_schema(url: str) -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


def _migrate_empty_database() -> None:
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")


async def _seed_and_exercise() -> None:
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import func, select, text

    from carepath.db import SessionLocal, engine
    from carepath.main import app
    from carepath.models import OfficialDataset, TreatmentPlan, User
    from carepath.seed import DEMO_PASSWORDS, seed_database

    await seed_database()

    async with SessionLocal() as session:
        revision = await session.scalar(text("SELECT version_num FROM alembic_version"))
        user_count = await session.scalar(select(func.count(User.id)))
        plan_count = await session.scalar(select(func.count(TreatmentPlan.id)))
        dataset_count = await session.scalar(select(func.count(OfficialDataset.id)))
        checksum = await session.scalar(select(OfficialDataset.checksum).limit(1))
    if not revision:
        _fail("alembic_version is empty after upgrade")
    if not user_count or not plan_count or not dataset_count:
        _fail(f"seed incomplete: users={user_count} plans={plan_count} datasets={dataset_count}")
    _ok(f"seed inserted {user_count} users, {plan_count} plans, {dataset_count} datasets")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://smoke") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"username": "patient", "password": DEMO_PASSWORDS["patient"]},
        )
        if login.status_code != 200:
            _fail(f"patient login returned {login.status_code}: {login.text[:200]}")
        patient_headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        _ok("patient login")

        dashboard = await client.get("/api/v1/patient/dashboard", headers=patient_headers)
        if dashboard.status_code != 200:
            _fail(f"patient dashboard returned {dashboard.status_code}")
        tasks = dashboard.json()["tasks"]
        if not tasks:
            _fail("patient dashboard has no tasks")
        _ok(f"patient dashboard returned {len(tasks)} tasks")

        pending = next((task for task in tasks if task["status"] != "COMPLETED"), None)
        if pending is None:
            _fail("no pending task to complete")
        completed = await client.post(
            f"/api/v1/tasks/{pending['id']}/complete",
            headers=patient_headers,
            json={"note": "postgres smoke"},
        )
        if completed.status_code != 200 or completed.json()["status"] != "COMPLETED":
            _fail(f"task completion failed: {completed.status_code} {completed.text[:200]}")
        _ok("patient task completed")

        regulator = await client.post(
            "/api/v1/auth/login",
            json={"username": "regulator", "password": DEMO_PASSWORDS["regulator"]},
        )
        if regulator.status_code != 200:
            _fail("regulator login failed")
        metrics = await client.get(
            "/api/v1/government/metrics",
            headers={"Authorization": f"Bearer {regulator.json()['accessToken']}"},
        )
        if metrics.status_code != 200:
            _fail(f"government metrics returned {metrics.status_code}")
        regions = metrics.json()["regions"]
        if not regions:
            _fail("government metrics returned no regions")
        if any("patientId" in row for row in regions):
            _fail("government metrics leaked patientId")
        _ok(f"government aggregation returned {len(regions)} regions without patient identifiers")

        admin = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": DEMO_PASSWORDS["admin"]},
        )
        if admin.status_code != 200:
            _fail("admin login failed")
        admin_headers = {"Authorization": f"Bearer {admin.json()['accessToken']}"}
        datasets = await client.get("/api/v1/admin/official-datasets", headers=admin_headers)
        if datasets.status_code != 200 or len(datasets.json()) < 4:
            _fail("official dataset listing failed")
        _ok("official dataset listing")

        duplicate = await client.post(
            "/api/v1/admin/official-datasets",
            headers=admin_headers,
            json={
                "sourceCode": "NMPA",
                "title": "duplicate smoke snapshot",
                "version": "smoke",
                "sourceUrl": "https://www.nmpa.gov.cn/",
                "checksum": checksum,
                "reviewer": "smoke",
                "content": {},
            },
        )
        if duplicate.status_code != 409:
            _fail(f"duplicate checksum returned {duplicate.status_code}, expected 409")
        _ok("duplicate official dataset rejected with 409")

        nmpa_payload = {
            "title": "国家药品监督管理局公开药品目录快照（冒烟）",
            "version": "smoke-2026-10",
            "sourceUrl": "https://www.nmpa.gov.cn/",
            "publishedAt": "2026-10-01",
            "effectiveAt": "2026-10-01",
            "records": [
                {
                    "approvalNumber": "国药准字H20260001",
                    "name": "示例降压片",
                    "manufacturer": "华康示范药业有限公司（虚构）",
                }
            ],
        }
        imported = await client.post(
            "/api/v1/admin/official-datasets/sources/NMPA/import",
            headers=admin_headers,
            json={"payload": nmpa_payload},
        )
        if imported.status_code != 201:
            _fail(f"source import returned {imported.status_code}: {imported.text[:200]}")
        if imported.json()["status"] != "VERIFIED":
            _fail("source import should be VERIFIED")
        duplicate_import = await client.post(
            "/api/v1/admin/official-datasets/sources/NMPA/import",
            headers=admin_headers,
            json={"payload": nmpa_payload},
        )
        if duplicate_import.status_code != 409:
            _fail(
                f"duplicate source import returned {duplicate_import.status_code}, expected 409"
            )
        _ok("official source import with duplicate rejection")

    await engine.dispose()


def main() -> int:
    url = _configure_environment()
    if not url:
        print("SKIP: set CAREPATH_SMOKE_DATABASE_URL to a postgresql+asyncpg:// URL")
        return 0

    print("STEP: reset schema", flush=True)
    asyncio.run(_reset_schema(url))
    print("STEP: alembic upgrade", flush=True)
    _migrate_empty_database()
    _ok("alembic upgrade head on empty PostgreSQL schema")
    print("STEP: seed and HTTP flow", flush=True)
    asyncio.run(_seed_and_exercise())
    print("DONE: PostgreSQL smoke passed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())