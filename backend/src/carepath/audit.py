from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from carepath.deps import CurrentUser
from carepath.models import AuditEvent


def add_audit(
    db: AsyncSession,
    current: CurrentUser,
    *,
    action: str,
    resource_kind: str,
    resource_id: str,
    patient_id: str | None = None,
    organization_id: str | None = None,
    request_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=current.user.id,
            actor_role=current.user.role,
            action=action,
            resource_kind=resource_kind,
            resource_id=resource_id,
            patient_id=patient_id,
            organization_id=organization_id or current.user.organization_id,
            request_id=request_id,
            detail=detail or {},
        )
    )
