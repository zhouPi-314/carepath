from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.deps import CurrentUser
from carepath.models import (
    Alert,
    CaregiverGrant,
    CareTask,
    MedicationSchedule,
    PatientProfile,
    TreatmentPlan,
    User,
)
from carepath.schemas import (
    AlertOut,
    CaregiverOut,
    CarePlanOut,
    MedicationOut,
    PatientDashboard,
    PatientOut,
    TaskOut,
)


def active_grant_filter(caregiver_user_id: str) -> tuple:
    now = datetime.now(UTC)
    return (
        CaregiverGrant.caregiver_user_id == caregiver_user_id,
        CaregiverGrant.active.is_(True),
        (CaregiverGrant.expires_at.is_(None) | (CaregiverGrant.expires_at > now)),
    )


async def patient_for_user(db: AsyncSession, user_id: str) -> PatientProfile | None:
    return await db.scalar(select(PatientProfile).where(PatientProfile.user_id == user_id))


async def accessible_patient_ids(
    db: AsyncSession,
    current: CurrentUser,
) -> set[str]:
    if current.user.role == "PATIENT":
        profile = await patient_for_user(db, current.user.id)
        return {profile.id} if profile else set()
    if current.user.role == "CAREGIVER":
        result = await db.scalars(
            select(CaregiverGrant).where(*active_grant_filter(current.user.id))
        )
        return {grant.patient_id for grant in result}
    if current.user.role == "DOCTOR":
        result = await db.scalars(
            select(TreatmentPlan.patient_id).where(
                TreatmentPlan.doctor_id == current.user.id,
                TreatmentPlan.organization_id == current.user.organization_id,
            )
        )
        return set(result)
    if current.user.role == "HOSPITAL_ADMIN":
        result = await db.scalars(
            select(TreatmentPlan.patient_id).where(
                TreatmentPlan.organization_id == current.user.organization_id,
            )
        )
        return set(result)
    return set()


async def caregiver_scopes(
    db: AsyncSession,
    current: CurrentUser,
    patient_id: str,
) -> set[str]:
    if current.user.role != "CAREGIVER":
        return {
            "tasks:read",
            "tasks:complete",
            "medications:read",
            "appointments:read",
            "observations:read",
            "observations:write",
        }
    grant = await db.scalar(
        select(CaregiverGrant).where(
            CaregiverGrant.patient_id == patient_id,
            *active_grant_filter(current.user.id),
        )
    )
    return set(grant.scopes) if grant else set()


async def ensure_patient_access(
    db: AsyncSession,
    current: CurrentUser,
    patient_id: str,
    scope: str,
) -> None:
    patient_ids = await accessible_patient_ids(db, current)
    if patient_id not in patient_ids:
        raise HTTPException(status_code=403, detail="无权访问该患者")
    scopes = await caregiver_scopes(db, current, patient_id)
    if current.user.role == "CAREGIVER" and scope not in scopes:
        raise HTTPException(status_code=403, detail="家属授权范围不足")


def task_is_overdue(task: CareTask, now: datetime | None = None) -> bool:
    if task.status in {"COMPLETED", "SKIPPED"}:
        return False
    now = now or datetime.now(UTC)
    due_at = task.due_at
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=UTC)
    return due_at < now


def task_out(task: CareTask) -> TaskOut:
    return TaskOut(
        id=task.id,
        plan_id=task.plan_id,
        patient_id=task.patient_id,
        title=task.title,
        description=task.description,
        category=task.category,
        due_at=task.due_at,
        status=task.status,
        is_overdue=task_is_overdue(task),
        completed_at=task.completed_at,
    )


async def build_patient_dashboard(
    db: AsyncSession,
    current: CurrentUser,
    patient_id: str | None = None,
) -> PatientDashboard:
    patient_ids = await accessible_patient_ids(db, current)
    if patient_id is None:
        profile = await patient_for_user(db, current.user.id)
        if profile:
            patient_id = profile.id
        elif patient_ids:
            patient_id = sorted(patient_ids)[0]
    if not patient_id or patient_id not in patient_ids:
        raise HTTPException(status_code=404, detail="未找到可访问患者")

    patient = await db.get(PatientProfile, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    plan = await db.scalar(
        select(TreatmentPlan)
        .where(TreatmentPlan.patient_id == patient_id)
        .order_by(TreatmentPlan.created_at.desc())
    )
    tasks_orm = list(
        (
            await db.scalars(
                select(CareTask)
                .where(CareTask.patient_id == patient_id)
                .order_by(CareTask.due_at.asc())
            )
        ).all()
    )
    meds_orm = list(
        (
            await db.scalars(
                select(MedicationSchedule)
                .where(MedicationSchedule.patient_id == patient_id)
                .order_by(MedicationSchedule.drug_name.asc())
            )
        ).all()
    )
    alerts_orm = list(
        (
            await db.scalars(
                select(Alert)
                .where(Alert.patient_id == patient_id)
                .order_by(Alert.created_at.desc())
                .limit(20)
            )
        ).all()
    )
    grants = list(
        (
            await db.scalars(
                select(CaregiverGrant)
                .where(
                    CaregiverGrant.patient_id == patient_id,
                    CaregiverGrant.active.is_(True),
                )
                .order_by(CaregiverGrant.created_at.desc())
            )
        ).all()
    )
    caregiver_ids = [grant.caregiver_user_id for grant in grants]
    caregiver_users = {}
    if caregiver_ids:
        caregiver_users = {
            user.id: user
            for user in (
                await db.scalars(select(User).where(User.id.in_(caregiver_ids)))
            ).all()
        }

    scopes = await caregiver_scopes(db, current, patient_id)
    if current.user.role == "CAREGIVER":
        if "tasks:read" not in scopes:
            tasks_orm = []
        if "medications:read" not in scopes:
            meds_orm = []

    return PatientDashboard(
        patient=PatientOut.model_validate(patient),
        plan=CarePlanOut.model_validate(plan) if plan else None,
        tasks=[task_out(task) for task in tasks_orm],
        medications=[
            MedicationOut(
                id=med.id,
                drug_name=med.drug_name,
                approval_number=med.approval_number,
                dose_text=med.dose_text,
                frequency_text=med.frequency_text,
                start_date=med.start_date,
                end_date=med.end_date,
                status=med.status,
            )
            for med in meds_orm
        ],
        alerts=[
            AlertOut(
                id=alert.id,
                type=alert.type,
                severity=alert.severity,
                title=alert.title,
                detail=alert.detail,
                status=alert.status,
                created_at=alert.created_at,
            )
            for alert in alerts_orm
        ],
        caregivers=[
            CaregiverOut(
                caregiver_user_id=grant.caregiver_user_id,
                display_name=caregiver_users[grant.caregiver_user_id].display_name
                if grant.caregiver_user_id in caregiver_users
                else "已注销用户",
                scopes=list(grant.scopes),
                active=grant.active,
                expires_at=grant.expires_at,
            )
            for grant in grants
        ],
    )
