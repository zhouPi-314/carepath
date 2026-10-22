from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.audit import add_audit
from carepath.db import get_db
from carepath.deps import CurrentUser, require_roles
from carepath.models import OfficialDataset
from carepath.schemas import OfficialDatasetCreate, OfficialDatasetOut

router = APIRouter(prefix="/admin", tags=["系统管理"])


@router.get("/official-datasets", response_model=list[OfficialDatasetOut])
async def list_official_datasets(
    current: CurrentUser = Depends(require_roles("SYSTEM_ADMIN", "REGULATOR")),
    db: AsyncSession = Depends(get_db),
) -> list[OfficialDatasetOut]:
    datasets = (
        await db.scalars(
            select(OfficialDataset).order_by(OfficialDataset.imported_at.desc())
        )
    ).all()
    return [OfficialDatasetOut.model_validate(item) for item in datasets]


@router.post("/official-datasets", response_model=OfficialDatasetOut, status_code=201)
async def import_official_dataset(
    payload: OfficialDatasetCreate,
    current: CurrentUser = Depends(require_roles("SYSTEM_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> OfficialDatasetOut:
    existing = await db.scalar(
        select(OfficialDataset).where(OfficialDataset.checksum == payload.checksum)
    )
    if existing:
        raise HTTPException(status_code=409, detail="相同校验值的数据快照已导入")
    dataset = OfficialDataset(
        source_code=payload.source_code,
        title=payload.title,
        version=payload.version,
        source_url=payload.source_url,
        published_at=payload.published_at,
        effective_at=payload.effective_at,
        imported_at=datetime.now(UTC),
        checksum=payload.checksum,
        reviewer=payload.reviewer,
        status="VERIFIED",
        content=payload.content,
    )
    db.add(dataset)
    await db.flush()
    add_audit(
        db,
        current,
        action="OFFICIAL_DATASET_IMPORT",
        resource_kind="official_dataset",
        resource_id=dataset.id,
        detail={"sourceCode": dataset.source_code, "version": dataset.version},
    )
    await db.commit()
    await db.refresh(dataset)
    return OfficialDatasetOut.model_validate(dataset)
