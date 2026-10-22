from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.audit import add_audit
from carepath.db import get_db
from carepath.deps import CurrentUser, require_roles
from carepath.models import OfficialDataset
from carepath.official_data.contracts import (
    DuplicateSnapshotError,
    SnapshotValidationError,
    UnsupportedSourceError,
)
from carepath.official_data.repository import SqlAlchemyOfficialDatasetRepository
from carepath.official_data.service import import_snapshot
from carepath.official_data.sources import get_source, supported_sources
from carepath.schemas import (
    OfficialDatasetCreate,
    OfficialDatasetOut,
    OfficialSourceImport,
    OfficialSourceOut,
)

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


@router.get("/official-datasets/sources", response_model=list[OfficialSourceOut])
async def list_official_sources(
    current: CurrentUser = Depends(require_roles("SYSTEM_ADMIN", "REGULATOR")),
) -> list[OfficialSourceOut]:
    return [OfficialSourceOut(**item) for item in supported_sources()]


@router.post(
    "/official-datasets/sources/{source_code}/import",
    response_model=OfficialDatasetOut,
    status_code=201,
)
async def import_official_source(
    source_code: str,
    payload: OfficialSourceImport,
    current: CurrentUser = Depends(require_roles("SYSTEM_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> OfficialDatasetOut:
    try:
        source = get_source(source_code)
    except UnsupportedSourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    repository = SqlAlchemyOfficialDatasetRepository(db)
    reviewer = (payload.reviewer or current.user.display_name).strip()
    try:
        snapshot = await import_snapshot(
            source,
            payload.payload,
            repository,
            reviewer=reviewer,
        )
    except SnapshotValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SNAPSHOT", "errors": exc.errors},
        ) from exc
    except DuplicateSnapshotError as exc:
        raise HTTPException(
            status_code=409,
            detail="相同校验值的数据快照已导入",
        ) from exc

    add_audit(
        db,
        current,
        action="OFFICIAL_DATASET_IMPORT",
        resource_kind="official_dataset",
        resource_id=snapshot.id or "",
        detail={
            "sourceCode": snapshot.source_code,
            "version": snapshot.version,
            "checksum": snapshot.checksum,
        },
    )
    await db.commit()
    row = await db.get(OfficialDataset, snapshot.id)
    if row is None:
        raise HTTPException(status_code=500, detail="官方数据快照写入失败")
    return OfficialDatasetOut.model_validate(row)


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
