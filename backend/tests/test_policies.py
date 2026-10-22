from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from carepath.policies import Action, Principal, Resource, can_access


@dataclass(frozen=True)
class Grant:
    patient_id: str
    caregiver_id: str
    scopes: frozenset[str]
    active: bool = True
    expires_at: datetime | None = None


def test_cross_organization_access_is_denied() -> None:
    principal = Principal(
        user_id="doctor-1",
        role="DOCTOR",
        organization_id="hospital-a",
    )
    resource = Resource(
        kind="treatment_plan",
        organization_id="hospital-b",
        patient_id="patient-1",
        owner_user_id="doctor-2",
    )

    assert not can_access(principal, Action.READ, resource, grants=[])


def test_caregiver_access_requires_active_scope() -> None:
    patient_id = str(uuid4())
    caregiver_id = str(uuid4())
    principal = Principal(
        user_id=caregiver_id,
        role="CAREGIVER",
        organization_id=None,
    )
    resource = Resource(
        kind="care_task",
        organization_id="hospital-a",
        patient_id=patient_id,
        owner_user_id=patient_id,
        required_scope="tasks:read",
    )
    expired = Grant(
        patient_id=patient_id,
        caregiver_id=caregiver_id,
        scopes=frozenset({"tasks:read"}),
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    assert not can_access(principal, Action.READ, resource, grants=[expired])

    active = Grant(
        patient_id=patient_id,
        caregiver_id=caregiver_id,
        scopes=frozenset({"tasks:read"}),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    assert can_access(principal, Action.READ, resource, grants=[active])


def test_regulator_cannot_read_patient_level_resource() -> None:
    principal = Principal(
        user_id="regulator-1",
        role="REGULATOR",
        organization_id="government-1",
    )
    resource = Resource(
        kind="treatment_plan",
        organization_id="hospital-a",
        patient_id="patient-1",
        owner_user_id="doctor-1",
    )

    assert not can_access(principal, Action.READ, resource, grants=[])
