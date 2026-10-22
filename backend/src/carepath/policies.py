from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol


class Action(StrEnum):
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"
    EXPORT = "export"


class GrantLike(Protocol):
    patient_id: str
    caregiver_id: str
    scopes: frozenset[str]
    active: bool
    expires_at: datetime | None


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str
    organization_id: str | None


@dataclass(frozen=True)
class Resource:
    kind: str
    organization_id: str | None
    patient_id: str | None = None
    owner_user_id: str | None = None
    required_scope: str | None = None


def _grant_is_active(grant: GrantLike, now: datetime) -> bool:
    if not grant.active:
        return False
    if grant.expires_at is None:
        return True
    expires_at = grant.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at > now


def can_access(
    principal: Principal,
    action: Action,
    resource: Resource,
    grants: list[GrantLike],
) -> bool:
    """Evaluate the intentionally small ABAC policy used by the MVP."""
    if principal.role == "PATIENT":
        return resource.owner_user_id == principal.user_id

    if principal.role == "CAREGIVER":
        if not resource.patient_id:
            return False
        now = datetime.now(UTC)
        return any(
            grant.patient_id == resource.patient_id
            and grant.caregiver_id == principal.user_id
            and _grant_is_active(grant, now)
            and (
                resource.required_scope is None
                or resource.required_scope in grant.scopes
            )
            for grant in grants
        )

    if principal.role in {"DOCTOR", "HOSPITAL_ADMIN"}:
        if resource.patient_id is None and resource.kind.startswith("aggregate"):
            return principal.organization_id == resource.organization_id
        return bool(
            principal.organization_id
            and principal.organization_id == resource.organization_id
        )

    if principal.role == "REGULATOR":
        return resource.kind.startswith("aggregate") and action == Action.READ

    if principal.role == "PHARMA":
        return bool(
            resource.kind.startswith(("pharma", "aggregate"))
            and principal.organization_id == resource.organization_id
        )

    if principal.role == "SYSTEM_ADMIN":
        return resource.kind.startswith(("official", "identity", "audit"))

    return False
