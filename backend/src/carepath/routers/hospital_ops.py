from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.audit import add_audit
from carepath.db import get_db
from carepath.deps import CurrentUser, require_roles
from carepath.models import (
    Organization,
    PatientProfile,
    PatientTransfer,
    TreatmentPlan,
    TreatmentRecord,
    User,
)
from carepath.schemas import (
    OrganizationMemberOut,
    PatientTagsUpdate,
    StaffCreate,
    TransferCreate,
    TransferOut,
    TreatmentRecordCreate,
    TreatmentRecordOut,
)
from carepath.security import hash_password

router = APIRouter(prefix="/hospital", tags=["医院工作台"])


def _organization_id(current: CurrentUser) -> str:
    if not current.user.organization_id:
        raise HTTPException(status_code=400, detail="账号未绑定医院")
    return current.user.organization_id


async def _patient_in_organization(db: AsyncSession, patient_id: str, org_id: str) -> bool:
    assigned = await db.scalar(
        select(TreatmentPlan.id).where(
            TreatmentPlan.patient_id == patient_id,
            TreatmentPlan.organization_id == org_id,
        )
    )
    return assigned is not None


@router.get("/staff", response_model=list[OrganizationMemberOut])
async def list_staff(
    current: CurrentUser = Depends(require_roles("HOSPITAL_ADMIN", "DOCTOR")),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationMemberOut]:
    members = (
        await db.scalars(
            select(User)
            .where(User.organization_id == _organization_id(current))
            .order_by(User.role.asc(), User.display_name.asc())
        )
    ).all()
    return [
        OrganizationMemberOut(
            id=member.id,
            username=member.username,
            display_name=member.display_name,
            role=member.role,
            active=member.active,
        )
        for member in members
    ]


@router.post("/staff", response_model=OrganizationMemberOut, status_code=201)
async def create_staff(
    payload: StaffCreate,
    current: CurrentUser = Depends(require_roles("HOSPITAL_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> OrganizationMemberOut:
    existing = await db.scalar(select(User.id).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")
    member = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=payload.role,
        organization_id=_organization_id(current),
    )
    db.add(member)
    await db.flush()
    add_audit(
        db,
        current,
        action="STAFF_CREATE",
        resource_kind="user",
        resource_id=member.id,
        organization_id=member.organization_id,
    )
    await db.commit()
    return OrganizationMemberOut(
        id=member.id,
        username=member.username,
        display_name=member.display_name,
        role=member.role,
        active=member.active,
    )


@router.patch("/patients/{patient_id}/tags")
async def update_patient_tags(
    patient_id: str,
    payload: PatientTagsUpdate,
    current: CurrentUser = Depends(require_roles("HOSPITAL_ADMIN", "DOCTOR")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    org_id = _organization_id(current)
    if not await _patient_in_organization(db, patient_id, org_id):
        raise HTTPException(status_code=403, detail="患者未归属当前医院")
    patient = await db.get(PatientProfile, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    patient.care_level = payload.care_level
    patient.tags = payload.tags
    add_audit(
        db,
        current,
        action="PATIENT_TAG_UPDATE",
        resource_kind="patient_profile",
        resource_id=patient.id,
        patient_id=patient.id,
        organization_id=org_id,
        detail={"careLevel": payload.care_level, "tags": payload.tags},
    )
    await db.commit()
    return {"id": patient.id, "careLevel": patient.care_level, "tags": patient.tags}


@router.get("/transfers", response_model=list[TransferOut])
async def list_transfers(
    current: CurrentUser = Depends(require_roles("HOSPITAL_ADMIN", "DOCTOR")),
    db: AsyncSession = Depends(get_db),
) -> list[TransferOut]:
    org_id = _organization_id(current)
    rows = (
        await db.scalars(
            select(PatientTransfer)
            .where(
                (PatientTransfer.from_organization_id == org_id)
                | (PatientTransfer.to_organization_id == org_id)
            )
            .order_by(PatientTransfer.created_at.desc())
        )
    ).all()
    return [TransferOut.model_validate(row) for row in rows]


@router.post("/transfers", response_model=TransferOut, status_code=201)
async def create_transfer(
    payload: TransferCreate,
    current: CurrentUser = Depends(require_roles("HOSPITAL_ADMIN", "DOCTOR")),
    db: AsyncSession = Depends(get_db),
) -> TransferOut:
    org_id = _organization_id(current)
    if not await _patient_in_organization(db, payload.patient_id, org_id):
        raise HTTPException(status_code=403, detail="患者未归属当前医院")
    target = await db.get(Organization, payload.to_organization_id)
    if not target:
        raise HTTPException(status_code=404, detail="转入机构不存在")
    transfer = PatientTransfer(
        patient_id=payload.patient_id,
        from_organization_id=org_id,
        to_organization_id=target.id,
        level=payload.level,
        status="PENDING",
        reason=payload.reason,
        created_by=current.user.id,
    )
    db.add(transfer)
    await db.flush()
    add_audit(
        db,
        current,
        action="PATIENT_TRANSFER",
        resource_kind="patient_transfer",
        resource_id=transfer.id,
        patient_id=transfer.patient_id,
        organization_id=org_id,
        detail={"to": target.id, "level": payload.level},
    )
    await db.commit()
    return TransferOut.model_validate(transfer)


@router.post("/treatment-records", response_model=TreatmentRecordOut, status_code=201)
async def create_treatment_record(
    payload: TreatmentRecordCreate,
    current: CurrentUser = Depends(require_roles("DOCTOR", "HOSPITAL_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> TreatmentRecordOut:
    org_id = _organization_id(current)
    plan = await db.get(TreatmentPlan, payload.plan_id)
    if not plan or plan.organization_id != org_id:
        raise HTTPException(status_code=403, detail="无权写入该计划")
    record = TreatmentRecord(
        plan_id=plan.id,
        patient_id=plan.patient_id,
        organization_id=org_id,
        author_id=current.user.id,
        record_type=payload.record_type,
        title=payload.title,
        content={"summary": payload.summary},
        visibility=payload.visibility,
    )
    db.add(record)
    await db.flush()
    add_audit(
        db,
        current,
        action="TREATMENT_RECORD_CREATE",
        resource_kind="treatment_record",
        resource_id=record.id,
        patient_id=plan.patient_id,
        organization_id=org_id,
    )
    await db.commit()
    return TreatmentRecordOut.model_validate(record)


@router.get("/treatment-records/{patient_id}", response_model=list[TreatmentRecordOut])
async def list_treatment_records(
    patient_id: str,
    current: CurrentUser = Depends(require_roles("DOCTOR", "HOSPITAL_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> list[TreatmentRecordOut]:
    org_id = _organization_id(current)
    if not await _patient_in_organization(db, patient_id, org_id):
        raise HTTPException(status_code=403, detail="患者未归属当前医院")
    rows = (
        await db.scalars(
            select(TreatmentRecord)
            .where(
                TreatmentRecord.patient_id == patient_id,
                TreatmentRecord.organization_id == org_id,
            )
            .order_by(TreatmentRecord.created_at.desc())
        )
    ).all()
    return [TreatmentRecordOut.model_validate(row) for row in rows]
