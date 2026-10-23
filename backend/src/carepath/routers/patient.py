from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.audit import add_audit
from carepath.db import get_db
from carepath.deps import CurrentUser, get_current_user, get_unit_of_work
from carepath.models import (
    Alert,
    CareTask,
    ConversationMessage,
    Observation,
    OutboxEvent,
    TreatmentPlan,
    TreatmentRecord,
)
from carepath.schemas import (
    AlertActionRequest,
    AlertOut,
    CompleteTaskRequest,
    MessageCreate,
    MessageOut,
    ObservationCreate,
    ObservationOut,
    PatientDashboard,
    TaskOut,
    TreatmentRecordOut,
)
from carepath.services import (
    accessible_patient_ids,
    build_patient_dashboard,
    ensure_patient_access,
    task_out,
)
from carepath.unit_of_work import SqlAlchemyUnitOfWork

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
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> TaskOut:
    session = uow.session
    task = await uow.care_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    await ensure_patient_access(session, current, task.patient_id, "tasks:complete")
    if task.status != "COMPLETED":
        task.status = "COMPLETED"
        task.completed_at = datetime.now(UTC)
        task.completed_by = current.user.id
        add_audit(
            session,
            current,
            action="TASK_COMPLETE",
            resource_kind="care_task",
            resource_id=task.id,
            patient_id=task.patient_id,
            organization_id=task.organization_id,
            detail={"note": payload.note},
        )
        session.add(
            OutboxEvent(
                organization_id=task.organization_id,
                patient_id=task.patient_id,
                event_type="TASK_COMPLETED",
                payload={"taskId": task.id, "planId": task.plan_id},
            )
        )
        await uow.commit()
        await session.refresh(task)
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


async def _ensure_plan_access(
    db: AsyncSession,
    current: CurrentUser,
    plan: TreatmentPlan,
) -> None:
    if current.user.role in {"PATIENT", "CAREGIVER"}:
        await ensure_patient_access(db, current, plan.patient_id, "tasks:read")
        return
    if current.user.role == "DOCTOR":
        if plan.organization_id != current.user.organization_id:
            raise HTTPException(status_code=403, detail="无权访问该计划")
        return
    if current.user.role == "HOSPITAL_ADMIN":
        if plan.organization_id != current.user.organization_id:
            raise HTTPException(status_code=403, detail="无权访问该计划")
        return
    raise HTTPException(status_code=403, detail="当前角色不得访问临床计划")


@router.get("/plans/{plan_id}/messages", response_model=list[MessageOut])
async def list_messages(
    plan_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageOut]:
    plan = await db.get(TreatmentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="治疗计划不存在")
    await _ensure_plan_access(db, current, plan)
    rows = (
        await db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.plan_id == plan_id)
            .order_by(ConversationMessage.created_at.asc())
        )
    ).all()
    return [MessageOut.model_validate(row) for row in rows]


@router.post("/plans/{plan_id}/messages", response_model=MessageOut, status_code=201)
async def create_message(
    plan_id: str,
    payload: MessageCreate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageOut:
    plan = await db.get(TreatmentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="治疗计划不存在")
    await _ensure_plan_access(db, current, plan)
    message = ConversationMessage(
        plan_id=plan.id,
        patient_id=plan.patient_id,
        sender_id=current.user.id,
        sender_role=current.user.role,
        content=payload.content,
    )
    db.add(message)
    await db.flush()
    add_audit(
        db,
        current,
        action="MESSAGE_CREATE",
        resource_kind="conversation_message",
        resource_id=message.id,
        patient_id=plan.patient_id,
        organization_id=plan.organization_id,
    )
    await db.commit()
    return MessageOut.model_validate(message)


@router.get("/patient/records", response_model=list[TreatmentRecordOut])
async def list_family_records(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TreatmentRecordOut]:
    patient_ids = await accessible_patient_ids(db, current)
    if not patient_ids:
        raise HTTPException(status_code=404, detail="未找到可访问患者")
    patient_id = sorted(patient_ids)[0]
    rows = (
        await db.scalars(
            select(TreatmentRecord)
            .where(
                TreatmentRecord.patient_id == patient_id,
                TreatmentRecord.visibility.in_(("FAMILY", "CARE_TEAM_AND_FAMILY")),
            )
            .order_by(TreatmentRecord.created_at.desc())
        )
    ).all()
    return [TreatmentRecordOut.model_validate(row) for row in rows]


@router.post("/plans/{plan_id}/messages/read")
async def mark_messages_read(
    plan_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    plan = await db.get(TreatmentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="治疗计划不存在")
    await _ensure_plan_access(db, current, plan)
    rows = (
        await db.scalars(
            select(ConversationMessage).where(
                ConversationMessage.plan_id == plan_id,
                ConversationMessage.sender_id != current.user.id,
                ConversationMessage.read_at.is_(None),
            )
        )
    ).all()
    now = datetime.now(UTC)
    for row in rows:
        row.read_at = now
    await db.commit()
    return {"updated": len(rows)}
