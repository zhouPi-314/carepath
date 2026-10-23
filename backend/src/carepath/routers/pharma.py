from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.audit import add_audit
from carepath.db import get_db
from carepath.deps import CurrentUser, require_roles
from carepath.models import (
    DeliveryOrder,
    DrugProduct,
    MedicationSchedule,
    Organization,
    SupplyCapacityReport,
    TreatmentPlan,
)
from carepath.schemas import (
    CapacityReportCreate,
    DemandSignalOut,
    DrugProductOut,
    PharmaDashboard,
    PharmaDeliveryOut,
    SupplyCapacityOut,
)

router = APIRouter(prefix="/pharma", tags=["药企"])


async def demand_signals(db: AsyncSession) -> list[DemandSignalOut]:
    rows = (
        await db.execute(
            select(MedicationSchedule, TreatmentPlan, Organization)
            .join(TreatmentPlan, TreatmentPlan.id == MedicationSchedule.plan_id)
            .join(Organization, Organization.id == MedicationSchedule.organization_id)
        )
    ).all()
    groups: dict[tuple[str, str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"organizations": set(), "patients": set()}
    )
    for schedule, _plan, organization in rows:
        period = schedule.start_date.strftime("%Y-%m")
        key = (organization.region_code, schedule.drug_name, period)
        groups[key]["organizations"].add(organization.id)
        groups[key]["patients"].add(schedule.patient_id)

    result: list[DemandSignalOut] = []
    for (region_code, drug_name, period), values in sorted(groups.items()):
        organization_count = len(values["organizations"])
        patient_months = len(values["patients"])
        published = organization_count >= 3 and patient_months >= 50
        result.append(
            DemandSignalOut(
                region_code=region_code,
                drug_name=drug_name,
                period=period,
                organization_count=organization_count,
                patient_months=patient_months if published else 0,
                published=published,
            )
        )
    return result


@router.get("/demand", response_model=dict)
async def demand(
    current: CurrentUser = Depends(require_roles("PHARMA")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    signals = await demand_signals(db)
    return {
        "signals": [
            signal.model_dump(by_alias=True)
            for signal in signals
            if signal.published
        ],
        "disclaimers": [
            "仅发布至少覆盖 3 家机构、50 个患者月的区域月度信号。",
            "需求信号用于教学演示，不包含患者、医生或医院级明细。",
        ],
    }


@router.get("/dashboard", response_model=PharmaDashboard)
async def dashboard(
    current: CurrentUser = Depends(require_roles("PHARMA")),
    db: AsyncSession = Depends(get_db),
) -> PharmaDashboard:
    if not current.user.organization_id:
        raise HTTPException(status_code=400, detail="药企账号未绑定机构")
    products = (
        await db.scalars(
            select(DrugProduct).where(
                DrugProduct.organization_id == current.user.organization_id
            )
        )
    ).all()
    reports = (
        await db.scalars(
            select(SupplyCapacityReport)
            .where(
                SupplyCapacityReport.organization_id
                == current.user.organization_id
            )
            .order_by(SupplyCapacityReport.created_at.desc())
        )
    ).all()
    signals = [signal for signal in await demand_signals(db) if signal.published]
    return PharmaDashboard(
        products=[DrugProductOut.model_validate(product) for product in products],
        demand_signals=signals,
        capacity_reports=[
            SupplyCapacityOut(
                id=report.id,
                product_id=report.product_id,
                region_code=report.region_code,
                period=report.period,
                capacity_units=report.capacity_units,
                status=report.status,
                created_at=report.created_at,
            )
            for report in reports
        ],
        disclaimers=[
            "药企端不得访问患者、医生或医院级明细。",
            "产能反馈仅在平台内流转，不对接真实生产或采购系统。",
        ],
    )


@router.get("/products", response_model=list[DrugProductOut])
async def products(
    current: CurrentUser = Depends(require_roles("PHARMA")),
    db: AsyncSession = Depends(get_db),
) -> list[DrugProductOut]:
    items = (
        await db.scalars(
            select(DrugProduct).where(
                DrugProduct.organization_id == current.user.organization_id
            )
        )
    ).all()
    return [DrugProductOut.model_validate(item) for item in items]


@router.post("/capacity", response_model=SupplyCapacityOut, status_code=201)
async def create_capacity_report(
    payload: CapacityReportCreate,
    current: CurrentUser = Depends(require_roles("PHARMA")),
    db: AsyncSession = Depends(get_db),
) -> SupplyCapacityOut:
    product = await db.get(DrugProduct, payload.product_id)
    if not product or product.organization_id != current.user.organization_id:
        raise HTTPException(status_code=404, detail="药品不存在")
    report = SupplyCapacityReport(
        organization_id=current.user.organization_id or "",
        product_id=product.id,
        region_code=payload.region_code,
        period=payload.period,
        capacity_units=payload.capacity_units,
        submitted_by=current.user.id,
    )
    db.add(report)
    add_audit(
        db,
        current,
        action="CAPACITY_SUBMIT",
        resource_kind="supply_capacity_report",
        resource_id=report.id,
        organization_id=report.organization_id,
        detail={"productId": product.id, "period": payload.period},
    )
    await db.commit()
    await db.refresh(report)
    return SupplyCapacityOut(
        id=report.id,
        product_id=report.product_id,
        region_code=report.region_code,
        period=report.period,
        capacity_units=report.capacity_units,
        status=report.status,
        created_at=report.created_at,
    )


@router.get("/deliveries", response_model=list[PharmaDeliveryOut])
async def list_deliveries(
    current: CurrentUser = Depends(require_roles("PHARMA")),
    db: AsyncSession = Depends(get_db),
) -> list[PharmaDeliveryOut]:
    rows = (
        await db.execute(
            select(DeliveryOrder, DrugProduct)
            .join(DrugProduct, DeliveryOrder.product_id == DrugProduct.id)
            .where(DrugProduct.organization_id == current.user.organization_id)
            .order_by(DeliveryOrder.created_at.desc())
        )
    ).all()
    return [
        PharmaDeliveryOut(
            id=order.id,
            patient_id=order.patient_id,
            product_id=order.product_id,
            product_name=product.name,
            status=order.status,
            address_region=order.address_region,
            note=order.note,
            created_at=order.created_at,
        )
        for order, product in rows
    ]


@router.post("/deliveries/{delivery_id}/confirm", response_model=PharmaDeliveryOut)
async def confirm_delivery(
    delivery_id: str,
    current: CurrentUser = Depends(require_roles("PHARMA")),
    db: AsyncSession = Depends(get_db),
) -> PharmaDeliveryOut:
    order = await db.get(DeliveryOrder, delivery_id)
    product = await db.get(DrugProduct, order.product_id) if order and order.product_id else None
    if not order or not product or product.organization_id != current.user.organization_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="无权处理该配送单")
    order.status = "CONFIRMED"
    await db.commit()
    return PharmaDeliveryOut(
        id=order.id,
        patient_id=order.patient_id,
        product_id=order.product_id,
        product_name=product.name,
        status=order.status,
        address_region=order.address_region,
        note=order.note,
        created_at=order.created_at,
    )
