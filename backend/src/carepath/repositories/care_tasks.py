from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.models import CareTask


class CareTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, task_id: str) -> CareTask | None:
        return await self._session.get(CareTask, task_id)

    async def list_for_patient(self, patient_id: str) -> list[CareTask]:
        return list(
            (
                await self._session.scalars(
                    select(CareTask)
                    .where(CareTask.patient_id == patient_id)
                    .order_by(CareTask.due_at.asc())
                )
            ).all()
        )

    async def list_for_plan(self, plan_id: str) -> list[CareTask]:
        return list(
            (
                await self._session.scalars(
                    select(CareTask).where(CareTask.plan_id == plan_id)
                )
            ).all()
        )

    async def list_for_patient_ids(self, patient_ids: Sequence[str]) -> list[CareTask]:
        if not patient_ids:
            return []
        return list(
            (
                await self._session.scalars(
                    select(CareTask).where(CareTask.patient_id.in_(patient_ids))
                )
            ).all()
        )
