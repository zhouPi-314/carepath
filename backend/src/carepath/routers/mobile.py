from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.db import get_db
from carepath.deps import CurrentUser, get_current_user
from carepath.models import (
    Alert,
    CareTask,
    CommunityTask,
    DeliveryOrder,
    DrugProduct,
    OfficialDataset,
    PatientTransfer,
    ReviewCase,
    SupplyCapacityReport,
    TreatmentPlan,
    TreatmentRecord,
    User,
    Volunteer,
)
from carepath.schemas import MobileItem, MobileMetric, MobileSummary

router = APIRouter(prefix="/mobile", tags=["移动端"])

IDENTITY = {
    "PATIENT": "病患",
    "CAREGIVER": "家属",
    "DOCTOR": "医生",
    "HOSPITAL_ADMIN": "医院管理员",
    "REGULATOR": "政府",
    "PHARMA": "药企",
    "COMMUNITY_ORG": "社区与志愿组织",
    "VOLUNTEER": "志愿者",
    "SYSTEM_ADMIN": "系统管理员",
}


async def _count(db: AsyncSession, statement) -> int:
    return int(await db.scalar(statement) or 0)


@router.get("/summary", response_model=MobileSummary)
async def summary(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileSummary:
    role = current.user.role
    label = IDENTITY.get(role, role)
    org_id = current.user.organization_id
    metrics: list[MobileMetric] = []
    items: list[MobileItem] = []

    if role in {"PATIENT", "CAREGIVER"}:
        patient_ids = await _patient_ids(db, current)
        open_tasks = await _count(
            db,
            select(func.count(CareTask.id)).where(
                CareTask.patient_id.in_(patient_ids),
                CareTask.status.notin_(("COMPLETED", "SKIPPED")),
            ),
        ) if patient_ids else 0
        open_alerts = await _count(
            db,
            select(func.count(Alert.id)).where(
                Alert.patient_id.in_(patient_ids), Alert.status == "OPEN"
            ),
        ) if patient_ids else 0
        metrics = [
            MobileMetric(label="待办任务", value=open_tasks),
            MobileMetric(label="未处理提醒", value=open_alerts),
        ]
        if patient_ids:
            tasks = (
                await db.scalars(
                    select(CareTask)
                    .where(CareTask.patient_id.in_(patient_ids))
                    .order_by(CareTask.due_at.asc())
                    .limit(5)
                )
            ).all()
            items = [
                MobileItem(title=task.title, detail=f"{task.category} · {task.status}")
                for task in tasks
            ]
        heading = "我的照护任务"

    elif role in {"DOCTOR", "HOSPITAL_ADMIN"}:
        if not org_id:
            heading = "医院工作台"
        else:
            plans = await _count(
                db,
                select(func.count(TreatmentPlan.id)).where(
                    TreatmentPlan.organization_id == org_id,
                    TreatmentPlan.status == "ACTIVE",
                ),
            )
            staff = await _count(
                db,
                select(func.count(User.id)).where(
                    User.organization_id == org_id, User.active.is_(True)
                ),
            )
            pending = await _count(
                db,
                select(func.count(PatientTransfer.id)).where(
                    PatientTransfer.to_organization_id == org_id,
                    PatientTransfer.status == "PENDING",
                ),
            )
            records = (
                await db.scalars(
                    select(TreatmentRecord)
                    .where(TreatmentRecord.organization_id == org_id)
                    .order_by(TreatmentRecord.created_at.desc())
                    .limit(5)
                )
            ).all()
            metrics = [
                MobileMetric(label="活跃计划", value=plans),
                MobileMetric(label="在岗职工", value=staff),
                MobileMetric(label="待接收转诊", value=pending),
            ]
            items = [
                MobileItem(title=record.title, detail=f"{record.record_type} · {record.visibility}")
                for record in records
            ]
            heading = "医院工作台"

    elif role == "VOLUNTEER" and org_id:
        volunteer = await db.scalar(select(Volunteer).where(Volunteer.user_id == current.user.id))
        tasks = []
        if volunteer:
            tasks = (
                await db.scalars(
                    select(CommunityTask)
                    .where(CommunityTask.assignee_id == volunteer.id)
                    .order_by(CommunityTask.created_at.desc())
                )
            ).all()
        deliveries = await _count(
            db,
            select(func.count(DeliveryOrder.id)).where(
                DeliveryOrder.organization_id == org_id, DeliveryOrder.status == "PENDING"
            ),
        )
        metrics = [
            MobileMetric(label="我的任务", value=len(tasks)),
            MobileMetric(
                label="待完成",
                value=sum(task.status == "OPEN" for task in tasks),
            ),
            MobileMetric(label="待配送", value=deliveries),
        ]
        items = [
            MobileItem(title=task.title, detail=f"{task.category} · {task.status}")
            for task in tasks
        ]
        heading = "志愿者任务"

    elif role == "COMMUNITY_ORG" and org_id:
        volunteers = await _count(
            db, select(func.count(Volunteer.id)).where(Volunteer.organization_id == org_id)
        )
        open_tasks = await _count(
            db,
            select(func.count(CommunityTask.id)).where(
                CommunityTask.organization_id == org_id, CommunityTask.status == "OPEN"
            ),
        )
        pending_deliveries = await _count(
            db,
            select(func.count(DeliveryOrder.id)).where(
                DeliveryOrder.organization_id == org_id, DeliveryOrder.status == "PENDING"
            ),
        )
        metrics = [
            MobileMetric(label="志愿者", value=volunteers),
            MobileMetric(label="待办任务", value=open_tasks),
            MobileMetric(label="待配送", value=pending_deliveries),
        ]
        tasks = (
            await db.scalars(
                select(CommunityTask)
                .where(CommunityTask.organization_id == org_id)
                .order_by(CommunityTask.created_at.desc())
                .limit(5)
            )
        ).all()
        items = [
            MobileItem(title=task.title, detail=f"{task.category} · {task.status}")
            for task in tasks
        ]
        heading = "社区照护与志愿调度"

    elif role == "PHARMA" and org_id:
        products = await _count(
            db, select(func.count(DrugProduct.id)).where(DrugProduct.organization_id == org_id)
        )
        capacity = await _count(
            db,
            select(func.count(SupplyCapacityReport.id)).where(
                SupplyCapacityReport.organization_id == org_id
            ),
        )
        metrics = [
            MobileMetric(label="药品目录", value=products),
            MobileMetric(label="产能反馈", value=capacity),
        ]
        rows = (
            await db.scalars(
                select(DrugProduct).where(DrugProduct.organization_id == org_id).limit(5)
            )
        ).all()
        items = [
            MobileItem(title=row.name, detail=f"{row.approval_number} · {row.verification_status}")
            for row in rows
        ]
        heading = "药品供应与产能"

    elif role == "REGULATOR":
        reviews = await _count(
            db, select(func.count(ReviewCase.id)).where(ReviewCase.status == "PENDING")
        )
        datasets = await _count(db, select(func.count(OfficialDataset.id)))
        metrics = [
            MobileMetric(label="待审核入驻", value=reviews),
            MobileMetric(label="官方快照", value=datasets),
        ]
        cases = (
            await db.scalars(
                select(ReviewCase).where(ReviewCase.status == "PENDING").limit(5)
            )
        ).all()
        items = [
            MobileItem(title=case.subject, detail=f"{case.type} · {case.status}")
            for case in cases
        ]
        heading = "入驻认证与区域监管"

    else:
        datasets = await _count(db, select(func.count(OfficialDataset.id)))
        metrics = [MobileMetric(label="官方快照", value=datasets)]
        heading = "系统管理"

    return MobileSummary(
        role=role,
        identity_label=label,
        heading=heading,
        metrics=metrics,
        items=items,
    )


async def _patient_ids(db: AsyncSession, current: CurrentUser) -> list[str]:
    from carepath.services import accessible_patient_ids

    return sorted(await accessible_patient_ids(db, current))
