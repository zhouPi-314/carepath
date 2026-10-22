"""SQLAlchemy adapter for the official dataset repository port."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.models import OfficialDataset
from carepath.official_data.contracts import DatasetSnapshot


class SqlAlchemyOfficialDatasetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_by_checksum(self, checksum: str) -> bool:
        found = await self._session.scalar(
            select(OfficialDataset.id).where(OfficialDataset.checksum == checksum)
        )
        return found is not None

    async def add(self, snapshot: DatasetSnapshot) -> str:
        row = OfficialDataset(
            source_code=snapshot.source_code,
            title=snapshot.title,
            version=snapshot.version,
            source_url=snapshot.source_url,
            published_at=snapshot.published_at,
            effective_at=snapshot.effective_at,
            checksum=snapshot.checksum,
            parser_version=snapshot.parser_version,
            reviewer=snapshot.reviewer,
            status=snapshot.status,
            content=snapshot.content,
        )
        self._session.add(row)
        await self._session.flush()
        return row.id
