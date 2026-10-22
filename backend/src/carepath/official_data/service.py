"""Application service that turns an exported snapshot into stored custody data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import date
from typing import Any

from carepath.official_data.contracts import (
    DatasetSnapshot,
    DuplicateSnapshotError,
    OfficialCatalogSource,
    OfficialDatasetRepository,
    SnapshotValidationError,
)
from carepath.official_data.normalization import (
    compute_checksum,
    derive_status,
    validate_snapshot,
)


async def import_snapshot(
    source: OfficialCatalogSource,
    raw: Mapping[str, Any],
    repository: OfficialDatasetRepository,
    *,
    reviewer: str,
    today: date | None = None,
) -> DatasetSnapshot:
    parsed = source.parse(raw)
    snapshot = DatasetSnapshot(
        source_code=parsed.source_code,
        title=parsed.title,
        version=parsed.version,
        source_url=parsed.source_url,
        published_at=parsed.published_at,
        effective_at=parsed.effective_at,
        checksum=compute_checksum(parsed.content),
        parser_version=parsed.parser_version,
        reviewer=reviewer.strip(),
        content=parsed.content,
        status=derive_status(parsed, today=today),
    )
    errors = validate_snapshot(snapshot, today=today)
    if errors:
        raise SnapshotValidationError(errors)
    if await repository.exists_by_checksum(snapshot.checksum):
        raise DuplicateSnapshotError(snapshot.checksum)
    dataset_id = await repository.add(snapshot)
    return replace(snapshot, id=dataset_id)
