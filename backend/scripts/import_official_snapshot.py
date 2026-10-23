"""Import a manually exported official public-data snapshot.

Usage:
    python scripts/import_official_snapshot.py NMPA path/to/nmpa.json \
        --reviewer "审核人" [--database-url sqlite+aiosqlite:///./carepath.db]

The target database schema must exist (run the app once or alembic upgrade head).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="导入官方公开数据 JSON 快照")
    parser.add_argument("source", choices=["NMPA", "NHSA", "NHC", "NBS"])
    parser.add_argument("file", type=Path, help="人工导出的 JSON 快照路径")
    parser.add_argument("--reviewer", default="manual-review", help="审核人（不能为空）")
    parser.add_argument("--database-url", default=None, help="覆盖 DATABASE_URL")
    args = parser.parse_args()

    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
    os.environ.setdefault("APP_ENV", "development")

    from carepath.db import SessionLocal, engine, init_db
    from carepath.official_data.contracts import OfficialDataError
    from carepath.official_data.repository import SqlAlchemyOfficialDatasetRepository
    from carepath.official_data.service import import_snapshot
    from carepath.official_data.sources import get_source

    async def run() -> int:
        try:
            await init_db()
            raw = json.loads(args.file.read_text(encoding="utf-8"))
            async with SessionLocal() as session:
                repository = SqlAlchemyOfficialDatasetRepository(session)
                try:
                    snapshot = await import_snapshot(
                        get_source(args.source),
                        raw,
                        repository,
                        reviewer=args.reviewer,
                    )
                except OfficialDataError as exc:
                    print(f"FAIL: {exc}")
                    return 1
                await session.commit()
                print(
                    "OK: "
                    f"source={snapshot.source_code} version={snapshot.version} "
                    f"status={snapshot.status} checksum={snapshot.checksum} id={snapshot.id}"
                )
                return 0
        finally:
            await engine.dispose()

    return asyncio.run(run())


if __name__ == "__main__":
    sys.exit(main())