from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class LoginRequest(CamelModel):
    username: str
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(CamelModel):
    refresh_token: str | None = None


class UserOut(CamelModel):
    id: str
    username: str
    display_name: str
    role: str
    organization_id: str | None
    organization_name: str | None = None
    identity_label: str | None = None


class LoginResponse(CamelModel):
    access_token: str
    refresh_token: str
    csrf_token: str
    user: UserOut


class OrganizationOut(CamelModel):
    id: str
    name: str
    type: str
    region_code: str
    verified: bool


class PatientOut(CamelModel):
    id: str
    display_name: str
    record_number: str
    region_code: str


class CarePlanOut(CamelModel):
    id: str
    title: str
    status: str
    version: int
    start_date: date
    end_date: date | None
    organization_id: str
    doctor_id: str
    content: dict[str, Any]


class CarePlanCreate(CamelModel):
    patient_id: str
    template_id: str
    title: str = Field(min_length=2, max_length=160)
    start_date: date


class CarePlanTemplateOut(CamelModel):
    id: str
    name: str
    condition_focus: str
    version: int
    status: str
    content: dict[str, Any]


class TaskOut(CamelModel):
    id: str
    plan_id: str
    patient_id: str
    title: str
    description: str
    category: str
    due_at: datetime
    status: str
    is_overdue: bool = False
    completed_at: datetime | None


class MedicationOut(CamelModel):
    id: str
    drug_name: str
    approval_number: str | None
    dose_text: str
    frequency_text: str
    start_date: date
    end_date: date | None
    status: str


class AlertOut(CamelModel):
    id: str
    type: str
    severity: str
    title: str
    detail: str
    status: str
    created_at: datetime


class CaregiverOut(CamelModel):
    caregiver_user_id: str
    display_name: str
    scopes: list[str]
    active: bool
    expires_at: datetime | None


class PatientDashboard(CamelModel):
    patient: PatientOut
    plan: CarePlanOut | None
    tasks: list[TaskOut]
    medications: list[MedicationOut]
    alerts: list[AlertOut]
    caregivers: list[CaregiverOut]


class CompleteTaskRequest(CamelModel):
    note: str = Field(default="", max_length=1000)


class ObservationCreate(CamelModel):
    plan_id: str
    type: str
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    measured_at: datetime | None = None


class ObservationOut(CamelModel):
    id: str
    plan_id: str
    patient_id: str
    type: str
    value_numeric: float | None
    value_text: str | None
    unit: str | None
    measured_at: datetime


class AlertActionRequest(CamelModel):
    note: str = Field(default="", max_length=1000)


class DoctorPatientRow(CamelModel):
    patient: PatientOut
    plan_id: str
    plan_status: str
    open_tasks: int
    open_alerts: int


class DoctorDashboard(CamelModel):
    active_plans: int
    patient_count: int
    open_alerts: int
    task_completion_rate: float
    patients: list[DoctorPatientRow]


class HospitalDashboard(CamelModel):
    organization: OrganizationOut
    active_plans: int
    doctor_count: int
    task_completion_rate: float
    open_alerts: int
    recent_alerts: list[AlertOut]


class OrganizationMemberOut(CamelModel):
    id: str
    username: str
    display_name: str
    role: str
    active: bool


class RegionMetric(CamelModel):
    region_code: str
    active_plans: int | None
    task_completion_rate: float | None
    open_alerts: int | None
    suppressed: bool


class GovernmentMetrics(CamelModel):
    generated_at: datetime
    minimum_cell_size: int = 10
    regions: list[RegionMetric]
    disclaimers: list[str]


class ReviewCaseOut(CamelModel):
    id: str
    organization_id: str
    type: str
    subject: str
    status: str
    decision_note: str | None
    created_at: datetime


class ReviewDecisionRequest(CamelModel):
    approved: bool
    note: str = Field(default="", max_length=1000)


class DrugProductOut(CamelModel):
    id: str
    name: str
    approval_number: str
    manufacturer: str
    verification_status: str
    status: str


class DemandSignalOut(CamelModel):
    region_code: str
    drug_name: str
    period: str
    organization_count: int
    patient_months: int
    published: bool


class SupplyCapacityOut(CamelModel):
    id: str
    product_id: str
    region_code: str
    period: str
    capacity_units: int
    status: str
    created_at: datetime


class PharmaDashboard(CamelModel):
    products: list[DrugProductOut]
    demand_signals: list[DemandSignalOut]
    capacity_reports: list[SupplyCapacityOut]
    disclaimers: list[str]


class CapacityReportCreate(CamelModel):
    product_id: str
    region_code: str
    period: str = Field(pattern=r"^\d{4}-\d{2}$")
    capacity_units: int = Field(ge=0)


class OfficialDatasetOut(CamelModel):
    id: str
    source_code: str
    title: str
    version: str
    source_url: str
    published_at: date | None
    effective_at: date | None
    imported_at: datetime
    checksum: str
    parser_version: str
    reviewer: str
    status: str


class OfficialDatasetCreate(CamelModel):
    source_code: str
    title: str
    version: str
    source_url: str
    published_at: date | None = None
    effective_at: date | None = None
    checksum: str = Field(min_length=16, max_length=128)
    reviewer: str
    content: dict[str, Any] = Field(default_factory=dict)


class OfficialSourceOut(CamelModel):
    source_code: str
    parser_version: str


class OfficialSourceImport(CamelModel):
    payload: dict[str, Any]
    reviewer: str | None = Field(default=None, max_length=80)


class TransferCreate(CamelModel):
    patient_id: str
    to_organization_id: str
    level: str = Field(default="COMMUNITY", max_length=24)
    reason: str = Field(default="", max_length=500)


class TransferOut(CamelModel):
    id: str
    patient_id: str
    from_organization_id: str
    to_organization_id: str
    level: str
    status: str
    reason: str
    created_at: datetime


class TreatmentRecordCreate(CamelModel):
    plan_id: str
    record_type: str = Field(default="PROGRESS", max_length=32)
    title: str = Field(min_length=2, max_length=160)
    summary: str = Field(default="", max_length=2000)
    visibility: str = Field(default="CARE_TEAM_AND_FAMILY", max_length=24)


class TreatmentRecordOut(CamelModel):
    id: str
    plan_id: str
    patient_id: str
    organization_id: str
    author_id: str
    record_type: str
    title: str
    content: dict[str, Any]
    visibility: str
    created_at: datetime


class MessageCreate(CamelModel):
    content: str = Field(min_length=1, max_length=2000)


class MessageOut(CamelModel):
    id: str
    plan_id: str
    sender_id: str
    sender_role: str
    content: str
    created_at: datetime


class StaffCreate(CamelModel):
    username: str = Field(min_length=3, max_length=80)
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern=r"^(DOCTOR|HOSPITAL_ADMIN)$")


class PatientTagsUpdate(CamelModel):
    care_level: str = Field(default="GENERAL", max_length=24)
    tags: list[str] = Field(default_factory=list)


class VolunteerCreate(CamelModel):
    name: str = Field(min_length=1, max_length=80)
    phone_masked: str = Field(default="", max_length=32)
    skills: list[str] = Field(default_factory=list)


class VolunteerOut(CamelModel):
    id: str
    name: str
    phone_masked: str
    skills: list[str]
    status: str


class CommunityTaskCreate(CamelModel):
    title: str = Field(min_length=2, max_length=160)
    category: str = Field(default="VISIT", max_length=32)
    patient_id: str | None = None
    assignee_id: str | None = None
    due_at: datetime | None = None


class CommunityTaskOut(CamelModel):
    id: str
    title: str
    category: str
    status: str
    patient_id: str | None
    assignee_id: str | None
    due_at: datetime | None
    created_at: datetime


class DeliveryCreate(CamelModel):
    patient_id: str | None = None
    product_id: str | None = None
    address_region: str = Field(default="", max_length=32)
    note: str = Field(default="", max_length=500)


class DeliveryOut(CamelModel):
    id: str
    patient_id: str | None
    product_id: str | None
    status: str
    address_region: str
    note: str
    created_at: datetime


class CommunityDashboard(CamelModel):
    organization_id: str
    volunteer_count: int
    open_task_count: int
    pending_delivery_count: int
    volunteers: list[VolunteerOut]
    tasks: list[CommunityTaskOut]
    deliveries: list[DeliveryOut]
