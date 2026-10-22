from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.audit import add_audit
from carepath.db import get_db
from carepath.deps import CurrentUser, require_roles
from carepath.models import (
    Alert,
    CareTask,
    Organization,
    ReviewCase,
    TreatmentPlan,
)
from carepath.schemas import (
    GovernmentMetrics,
    RegionMetric,
    ReviewCaseOut,
    ReviewDecisionRequest,
)

router = APIRouter(prefix="/government", tags=["政府监管"])


@router.get("/metrics", response_model=GovernmentMetrics)
async def metrics(
    current: CurrentUser = Depends(require_roles("REGULATOR")),
    db: AsyncSession = Depends(get_db),
) -> GovernmentMetrics:
    plans = (
        await db.scalars(
            select(TreatmentPlan).where(TreatmentPlan.status == "ACTIVE")
        )
    ).all()
    organizations = {
        organization.id: organization
        for organization in (await db.scalars(select(Organization))).all()
    }
    by_region: dict[str, list[TreatmentPlan]] = defaultdict(list)
    for plan in plans:
        organization = organizations.get(plan.organization_id)
        if organization:
            by_region[organization.region_code].append(plan)

    result: list[RegionMetric] = []
    for region_code, region_plans in sorted(by_region.items()):
        plan_ids = [plan.id for plan in region_plans]
        tasks = (
            await db.scalars(select(CareTask).where(CareTask.plan_id.in_(plan_ids)))
        ).all()
        open_alerts = len(
            (
                await db.scalars(
                    select(Alert.id).where(
                        Alert.plan_id.in_(plan_ids),
                        Alert.status == "OPEN",
                    )
                )
            ).all()
        )
        suppressed = len(region_plans) < 10
        result.append(
            RegionMetric(
                region_code=region_code,
                active_plans=None if suppressed else len(region_plans),
                task_completion_rate=(
                    None
                    if suppressed or not tasks
                    else sum(task.status == "COMPLETED" for task in tasks) / len(tasks)
                ),
                open_alerts=None if suppressed else open_alerts,
                suppressed=suppressed,
            )
        )
    return GovernmentMetrics(
        generated_at=datetime.now(UTC),
        regions=result,
        disclaimers=[
            "聚合数据仅用于课程演示，不代表真实医保、卫健或行政统计。",
            "计数小于 10 的区域被整体抑制；百分比和提醒数不作为监管结论。",
        ],
    )


@router.get("/reviews", response_model=list[ReviewCaseOut])
async def reviews(
    current: CurrentUser = Depends(require_roles("REGULATOR")),
    db: AsyncSession = Depends(get_db),
) -> list[ReviewCaseOut]:
    cases = (
        await db.scalars(
            select(ReviewCase).order_by(ReviewCase.created_at.desc())
        )
    ).all()
    return [ReviewCaseOut.model_validate(case) for case in cases]


@router.post("/reviews/{case_id}/decision", response_model=ReviewCaseOut)
async def decide_review(
    case_id: str,
    payload: ReviewDecisionRequest,
    current: CurrentUser = Depends(require_roles("REGULATOR")),
    db: AsyncSession = Depends(get_db),
) -> ReviewCaseOut:
    case = await db.get(ReviewCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="审核案件不存在")
    case.status = "APPROVED" if payload.approved else "REJECTED"
    case.decision_note = payload.note
    case.reviewed_by = current.user.id
    case.reviewed_at = datetime.now(UTC)
    organization = await db.get(Organization, case.organization_id)
    if payload.approved and organization:
        organization.verified = True
    add_audit(
        db,
        current,
        action="REVIEW_DECISION",
        resource_kind="review_case",
        resource_id=case.id,
        organization_id=case.organization_id,
        detail={"approved": payload.approved, "note": payload.note},
    )
    await db.commit()
    await db.refresh(case)
    return ReviewCaseOut.model_validate(case)
