from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.db import get_db
from carepath.deps import CurrentUser, require_roles
from carepath.models import CommunityTask, DeliveryOrder, Volunteer
from carepath.schemas import (
    CommunityDashboard,
    CommunityTaskCreate,
    CommunityTaskOut,
    DeliveryCreate,
    DeliveryOut,
    VolunteerCreate,
    VolunteerOut,
)

router = APIRouter(prefix="/community", tags=["社区与志愿组织"])


def _org_id(current: CurrentUser) -> str:
    if not current.user.organization_id:
        raise ValueError("账号未绑定社区组织")
    return current.user.organization_id


@router.get("/dashboard", response_model=CommunityDashboard)
async def dashboard(
    current: CurrentUser = Depends(require_roles("COMMUNITY_ORG")),
    db: AsyncSession = Depends(get_db),
) -> CommunityDashboard:
    org_id = _org_id(current)
    volunteers = (
        await db.scalars(
            select(Volunteer)
            .where(Volunteer.organization_id == org_id)
            .order_by(Volunteer.created_at.desc())
        )
    ).all()
    tasks = (
        await db.scalars(
            select(CommunityTask)
            .where(CommunityTask.organization_id == org_id)
            .order_by(CommunityTask.created_at.desc())
        )
    ).all()
    deliveries = (
        await db.scalars(
            select(DeliveryOrder)
            .where(DeliveryOrder.organization_id == org_id)
            .order_by(DeliveryOrder.created_at.desc())
        )
    ).all()
    open_tasks = sum(task.status == "OPEN" for task in tasks)
    pending_deliveries = sum(order.status == "PENDING" for order in deliveries)
    return CommunityDashboard(
        organization_id=org_id,
        volunteer_count=len(volunteers),
        open_task_count=open_tasks,
        pending_delivery_count=pending_deliveries,
        volunteers=[
            VolunteerOut(
                id=item.id,
                name=item.name,
                phone_masked=item.phone_masked,
                skills=list(item.skills or []),
                status=item.status,
            )
            for item in volunteers
        ],
        tasks=[CommunityTaskOut.model_validate(item) for item in tasks],
        deliveries=[DeliveryOut.model_validate(item) for item in deliveries],
    )


@router.post("/volunteers", response_model=VolunteerOut, status_code=201)
async def create_volunteer(
    payload: VolunteerCreate,
    current: CurrentUser = Depends(require_roles("COMMUNITY_ORG")),
    db: AsyncSession = Depends(get_db),
) -> VolunteerOut:
    volunteer = Volunteer(
        organization_id=_org_id(current),
        name=payload.name,
        phone_masked=payload.phone_masked,
        skills=payload.skills,
    )
    db.add(volunteer)
    await db.commit()
    return VolunteerOut(
        id=volunteer.id,
        name=volunteer.name,
        phone_masked=volunteer.phone_masked,
        skills=list(volunteer.skills or []),
        status=volunteer.status,
    )


@router.post("/tasks", response_model=CommunityTaskOut, status_code=201)
async def create_task(
    payload: CommunityTaskCreate,
    current: CurrentUser = Depends(require_roles("COMMUNITY_ORG")),
    db: AsyncSession = Depends(get_db),
) -> CommunityTaskOut:
    task = CommunityTask(
        organization_id=_org_id(current),
        patient_id=payload.patient_id,
        title=payload.title,
        category=payload.category,
        assignee_id=payload.assignee_id,
        due_at=payload.due_at,
    )
    db.add(task)
    await db.commit()
    return CommunityTaskOut.model_validate(task)


@router.post("/deliveries", response_model=DeliveryOut, status_code=201)
async def create_delivery(
    payload: DeliveryCreate,
    current: CurrentUser = Depends(require_roles("COMMUNITY_ORG")),
    db: AsyncSession = Depends(get_db),
) -> DeliveryOut:
    order = DeliveryOrder(
        organization_id=_org_id(current),
        patient_id=payload.patient_id,
        product_id=payload.product_id,
        address_region=payload.address_region,
        note=payload.note,
    )
    db.add(order)
    await db.commit()
    return DeliveryOut.model_validate(order)
