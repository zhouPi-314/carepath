from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.audit import add_audit
from carepath.db import get_db
from carepath.deps import CurrentUser, get_current_user, require_roles
from carepath.models import (
    Alert,
    CarePlanTemplate,
    CareTask,
    MedicationSchedule,
    Organization,
    PatientConsent,
    PatientProfile,
    TreatmentPlan,
    User,
)
from carepath.schemas import (
    AlertActionRequest,
    AlertOut,
    CarePlanCreate,
    CarePlanOut,
    CarePlanTemplateOut,
    DoctorDashboard,
    DoctorPatientRow,
    HospitalDashboard,
    OrganizationMemberOut,
    OrganizationOut,
    PatientOut,
)

router = APIRouter(tags=["医生与医院"])


@router.get("/care-plan-templates", response_model=list[CarePlanTemplateOut])
async def list_templates(
    current: CurrentUser = Depends(require_roles("DOCTOR", "HOSPITAL_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> list[CarePlanTemplateOut]:
    templates = (
        await db.scalars(
            select(CarePlanTemplate)
            .where(CarePlanTemplate.status == "PUBLISHED")
            .order_by(CarePlanTemplate.name.asc())
        )
    ).all()
    return [CarePlanTemplateOut.model_validate(item) for item in templates]


@router.get("/doctor/dashboard", response_model=DoctorDashboard)
async def doctor_dashboard(
    current: CurrentUser = Depends(require_roles("DOCTOR")),
    db: AsyncSession = Depends(get_db),
) -> DoctorDashboard:
    plans = list(
        (
            await db.scalars(
                select(TreatmentPlan)
                .where(TreatmentPlan.doctor_id == current.user.id)
                .order_by(TreatmentPlan.created_at.desc())
            )
        ).all()
    )
    patient_ids = [plan.patient_id for plan in plans]
    patients = {}
    if patient_ids:
        patients = {
            patient.id: patient
            for patient in (
                await db.scalars(
                    select(PatientProfile).where(PatientProfile.id.in_(patient_ids))
                )
            ).all()
        }
    task_total = 0
    task_completed = 0
    rows: list[DoctorPatientRow] = []
    for plan in plans:
        tasks = list(
            (
                await db.scalars(select(CareTask).where(CareTask.plan_id == plan.id))
            ).all()
        )
        open_tasks = sum(task.status not in {"COMPLETED", "SKIPPED"} for task in tasks)
        open_alerts = int(
            await db.scalar(
                select(func.count(Alert.id)).where(
                    Alert.plan_id == plan.id,
                    Alert.status == "OPEN",
                )
            )
            or 0
        )
        task_total += len(tasks)
        task_completed += sum(task.status == "COMPLETED" for task in tasks)
        if plan.patient_id in patients:
            rows.append(
                DoctorPatientRow(
                    patient=PatientOut.model_validate(patients[plan.patient_id]),
                    plan_id=plan.id,
                    plan_status=plan.status,
                    open_tasks=open_tasks,
                    open_alerts=open_alerts,
                )
            )
    open_alerts = sum(row.open_alerts for row in rows)
    return DoctorDashboard(
        active_plans=sum(plan.status == "ACTIVE" for plan in plans),
        patient_count=len(patients),
        open_alerts=open_alerts,
        task_completion_rate=(task_completed / task_total) if task_total else 0,
        patients=rows,
    )


@router.post("/treatment-plans", response_model=CarePlanOut, status_code=201)
async def create_treatment_plan(
    payload: CarePlanCreate,
    current: CurrentUser = Depends(require_roles("DOCTOR")),
    db: AsyncSession = Depends(get_db),
) -> CarePlanOut:
    template = await db.get(CarePlanTemplate, payload.template_id)
    patient = await db.get(PatientProfile, payload.patient_id)
    if not template or template.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="模板不可用")
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    assignment = await db.scalar(
        select(TreatmentPlan.id).where(
            TreatmentPlan.patient_id == patient.id,
            TreatmentPlan.organization_id == current.user.organization_id,
        )
    )
    if not assignment:
        raise HTTPException(status_code=403, detail="患者尚未归属当前医院")
    plan = TreatmentPlan(
        template_id=template.id,
        patient_id=patient.id,
        doctor_id=current.user.id,
        organization_id=current.user.organization_id or "",
        title=payload.title,
        status="ACTIVE",
        start_date=payload.start_date,
        content=template.content,
    )
    db.add(plan)
    await db.flush()
    db.add(
        PatientConsent(
            plan_id=plan.id,
            patient_id=patient.id,
            status="PENDING",
        )
    )
    for index, item in enumerate(template.content.get("tasks", []), start=1):
        db.add(
            CareTask(
                plan_id=plan.id,
                patient_id=patient.id,
                organization_id=plan.organization_id,
                title=item.get("title", f"任务 {index}"),
                description=item.get("description", ""),
                category=item.get("category", "SELF_CARE"),
                due_at=datetime.now(UTC)
                + timedelta(days=int(item.get("dueAfterDays", index))),
            )
        )
    for item in template.content.get("medications", []):
        db.add(
            MedicationSchedule(
                plan_id=plan.id,
                patient_id=patient.id,
                organization_id=plan.organization_id,
                drug_name=item["drugName"],
                approval_number=item.get("approvalNumber"),
                dose_text=item.get("doseText", ""),
                frequency_text=item.get("frequencyText", ""),
                start_date=payload.start_date,
                end_date=None,
            )
        )
    add_audit(
        db,
        current,
        action="PLAN_CREATE",
        resource_kind="treatment_plan",
        resource_id=plan.id,
        patient_id=patient.id,
        organization_id=plan.organization_id,
        detail={"templateId": template.id},
    )
    await db.commit()
    await db.refresh(plan)
    return CarePlanOut.model_validate(plan)


@router.get("/treatment-plans/{plan_id}", response_model=CarePlanOut)
async def get_treatment_plan(
    plan_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarePlanOut:
    plan = await db.get(TreatmentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="治疗计划不存在")
    if current.user.role in {"DOCTOR", "HOSPITAL_ADMIN"}:
        allowed = plan.organization_id == current.user.organization_id
        if current.user.role == "DOCTOR":
            allowed = allowed and plan.doctor_id == current.user.id
    else:
        raise HTTPException(status_code=403, detail="当前角色不得查看临床计划")
    if not allowed:
        raise HTTPException(status_code=403, detail="无权访问该计划")
    return CarePlanOut.model_validate(plan)


@router.get("/hospital/dashboard", response_model=HospitalDashboard)
async def hospital_dashboard(
    current: CurrentUser = Depends(require_roles("HOSPITAL_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> HospitalDashboard:
    organization = await db.get(Organization, current.user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="机构不存在")
    plans = list(
        (
            await db.scalars(
                select(TreatmentPlan).where(
                    TreatmentPlan.organization_id == organization.id
                )
            )
        ).all()
    )
    plan_ids = [plan.id for plan in plans]
    tasks = (
        list(
            (
                await db.scalars(
                    select(CareTask).where(CareTask.plan_id.in_(plan_ids))
                )
            ).all()
        )
        if plan_ids
        else []
    )
    alerts = list(
        (
            await db.scalars(
                select(Alert)
                .where(Alert.organization_id == organization.id)
                .order_by(Alert.created_at.desc())
                .limit(10)
            )
        ).all()
    )
    doctor_count = int(
        await db.scalar(
            select(func.count(User.id)).where(
                User.organization_id == organization.id,
                User.role == "DOCTOR",
                User.active.is_(True),
            )
        )
        or 0
    )
    return HospitalDashboard(
        organization=OrganizationOut.model_validate(organization),
        active_plans=sum(plan.status == "ACTIVE" for plan in plans),
        doctor_count=doctor_count,
        task_completion_rate=(
            sum(task.status == "COMPLETED" for task in tasks) / len(tasks)
            if tasks
            else 0
        ),
        open_alerts=sum(alert.status == "OPEN" for alert in alerts),
        recent_alerts=[
            AlertOut(
                id=alert.id,
                type=alert.type,
                severity=alert.severity,
                title=alert.title,
                detail=alert.detail,
                status=alert.status,
                created_at=alert.created_at,
            )
            for alert in alerts
        ],
    )


@router.get("/organizations/{organization_id}/members", response_model=list[OrganizationMemberOut])
async def organization_members(
    organization_id: str,
    current: CurrentUser = Depends(require_roles("HOSPITAL_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationMemberOut]:
    if current.user.organization_id != organization_id:
        raise HTTPException(status_code=403, detail="不得查看其他机构成员")
    members = (
        await db.scalars(
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.role.asc(), User.display_name.asc())
        )
    ).all()
    return [
        OrganizationMemberOut(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            active=user.active,
        )
        for user in members
    ]


@router.get("/doctor/alerts", response_model=list[AlertOut])
async def doctor_alerts(
    current: CurrentUser = Depends(require_roles("DOCTOR")),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    alerts = (
        await db.scalars(
            select(Alert)
            .join(TreatmentPlan, TreatmentPlan.id == Alert.plan_id)
            .where(TreatmentPlan.doctor_id == current.user.id)
            .order_by(Alert.created_at.desc())
        )
    ).all()
    return [
        AlertOut(
            id=alert.id,
            type=alert.type,
            severity=alert.severity,
            title=alert.title,
            detail=alert.detail,
            status=alert.status,
            created_at=alert.created_at,
        )
        for alert in alerts
    ]


@router.post("/doctor/alerts/{alert_id}/acknowledge", response_model=AlertOut)
async def doctor_acknowledge_alert(
    alert_id: str,
    payload: AlertActionRequest,
    current: CurrentUser = Depends(require_roles("DOCTOR")),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="提醒不存在")
    plan = await db.get(TreatmentPlan, alert.plan_id)
    if not plan or plan.doctor_id != current.user.id:
        raise HTTPException(status_code=403, detail="无权处理该提醒")
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
