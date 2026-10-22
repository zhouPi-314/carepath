from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.models import PatientProfile


class PatientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, patient_id: str) -> PatientProfile | None:
        return await self._session.get(PatientProfile, patient_id)

    async def get_by_user(self, user_id: str) -> PatientProfile | None:
        return await self._session.scalar(
            select(PatientProfile).where(PatientProfile.user_id == user_id)
        )

    async def list_by_ids(self, patient_ids: Sequence[str]) -> list[PatientProfile]:
        if not patient_ids:
            return []
        return list(
            (
                await self._session.scalars(
                    select(PatientProfile).where(PatientProfile.id.in_(patient_ids))
                )
            ).all()
        )
