from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.models import TreatmentPlan


class TreatmentPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, plan_id: str) -> TreatmentPlan | None:
        return await self._session.get(TreatmentPlan, plan_id)

    async def latest_for_patient(self, patient_id: str) -> TreatmentPlan | None:
        return await self._session.scalar(
            select(TreatmentPlan)
            .where(TreatmentPlan.patient_id == patient_id)
            .order_by(TreatmentPlan.created_at.desc())
        )

    async def list_for_doctor(self, doctor_id: str) -> list[TreatmentPlan]:
        return list(
            (
                await self._session.scalars(
                    select(TreatmentPlan)
                    .where(TreatmentPlan.doctor_id == doctor_id)
                    .order_by(TreatmentPlan.created_at.desc())
                )
            ).all()
        )

    async def list_for_organization(self, organization_id: str) -> list[TreatmentPlan]:
        return list(
            (
                await self._session.scalars(
                    select(TreatmentPlan).where(
                        TreatmentPlan.organization_id == organization_id
                    )
                )
            ).all()
        )

    async def patient_is_assigned(self, patient_id: str, organization_id: str) -> bool:
        found = await self._session.scalar(
            select(TreatmentPlan.id).where(
                TreatmentPlan.patient_id == patient_id,
                TreatmentPlan.organization_id == organization_id,
            )
        )
        return found is not None
