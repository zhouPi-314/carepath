from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.audit import add_audit
from carepath.db import get_db
from carepath.deps import CurrentUser, get_current_user
from carepath.models import Alert, CareTask, Observation, OutboxEvent, TreatmentPlan
from carepath.schemas import (
    AlertActionRequest,
    AlertOut,
    CompleteTaskRequest,
    ObservationCreate,
    ObservationOut,
    PatientDashboard,
    TaskOut,
)
from carepath.services import build_patient_dashboard, ensure_patient_access, task_out

router = APIRouter(tags=["患者与家属"])


@router.get("/patient/dashboard", response_model=PatientDashboard)
async def patient_dashboard(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientDashboard:
    return await build_patient_dashboard(db, current)


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskOut:
    task = await db.get(CareTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    await ensure_patient_access(db, current, task.patient_id, "tasks:read")
    return task_out(task)


@router.post("/tasks/{task_id}/complete", response_model=TaskOut)
async def complete_task(
    task_id: str,
    payload: CompleteTaskRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskOut:
    task = await db.get(CareTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    await ensure_patient_access(db, current, task.patient_id, "tasks:complete")
    if task.status != "COMPLETED":
        task.status = "COMPLETED"
        task.completed_at = datetime.now(UTC)
        task.completed_by = current.user.id
        add_audit(
            db,
            current,
            action="TASK_COMPLETE",
            resource_kind="care_task",
            resource_id=task.id,
            patient_id=task.patient_id,
            organization_id=task.organization_id,
            detail={"note": payload.note},
        )
        db.add(
            OutboxEvent(
                organization_id=task.organization_id,
                patient_id=task.patient_id,
                event_type="TASK_COMPLETED",
                payload={"taskId": task.id, "planId": task.plan_id},
            )
        )
        await db.commit()
        await db.refresh(task)
    return task_out(task)


@router.post("/observations", response_model=ObservationOut)
async def add_observation(
    payload: ObservationCreate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ObservationOut:
    plan = await db.get(TreatmentPlan, payload.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="治疗计划不存在")
    await ensure_patient_access(db, current, plan.patient_id, "observations:write")
    measured_at = payload.measured_at or datetime.now(UTC)
    observation = Observation(
        plan_id=plan.id,
        patient_id=plan.patient_id,
        organization_id=plan.organization_id,
        type=payload.type,
        value_numeric=payload.value_numeric,
        value_text=payload.value_text,
        unit=payload.unit,
        measured_at=measured_at,
        submitted_by=current.user.id,
    )
    db.add(observation)
    add_audit(
        db,
        current,
        action="OBSERVATION_CREATE",
        resource_kind="observation",
        resource_id=observation.id,
        patient_id=plan.patient_id,
        organization_id=plan.organization_id,
        detail={"type": payload.type},
    )
    await db.commit()
    await db.refresh(observation)
    return ObservationOut.model_validate(observation)


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    dashboard = await build_patient_dashboard(db, current)
    return dashboard.alerts


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: str,
    payload: AlertActionRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="提醒不存在")
    await ensure_patient_access(db, current, alert.patient_id, "tasks:read")
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = current.user.id
    alert.acknowledged_at = datetime.now(UTC)
    add_audit(
        db,
        current,
        action="ALERT_ACKNOWLEDGE",
        resource_kind="alert",
        resource_id=alert.id,
        patient_id=alert.patient_id,
        organization_id=alert.organization_id,
        detail={"note": payload.note},
    )
    await db.commit()
    await db.refresh(alert)
    return AlertOut(
        id=alert.id,
        type=alert.type,
        severity=alert.severity,
        title=alert.title,
        detail=alert.detail,
        status=alert.status,
        created_at=alert.created_at,
    )
