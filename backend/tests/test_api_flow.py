from __future__ import annotations

import pytest
from httpx import AsyncClient


async def login(client: AsyncClient, username: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "CarePath123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_caregiver_and_doctor_complete_task_flow(client: AsyncClient) -> None:
    caregiver = await login(client, "caregiver")
    headers = {"Authorization": f"Bearer {caregiver['accessToken']}"}

    dashboard = await client.get("/api/v1/patient/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    tasks = dashboard.json()["tasks"]
    target = next(task for task in tasks if task["status"] != "COMPLETED")

    completed = await client.post(
        f"/api/v1/tasks/{target['id']}/complete",
        headers=headers,
        json={"note": "家属确认已完成"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"

    doctor = await login(client, "doctor")
    doctor_headers = {"Authorization": f"Bearer {doctor['accessToken']}"}
    doctor_dashboard = await client.get("/api/v1/doctor/dashboard", headers=doctor_headers)
    assert doctor_dashboard.status_code == 200
    assert doctor_dashboard.json()["taskCompletionRate"] >= 0


@pytest.mark.asyncio
async def test_regulator_and_pharma_only_receive_aggregates(client: AsyncClient) -> None:
    regulator = await login(client, "regulator")
    regulator_headers = {"Authorization": f"Bearer {regulator['accessToken']}"}
    metrics = await client.get("/api/v1/government/metrics", headers=regulator_headers)
    assert metrics.status_code == 200, metrics.text
    assert all("patientId" not in row for row in metrics.json()["regions"])

    pharma = await login(client, "pharma")
    pharma_headers = {"Authorization": f"Bearer {pharma['accessToken']}"}
    demand = await client.get("/api/v1/pharma/demand", headers=pharma_headers)
    assert demand.status_code == 200, demand.text
    assert all("patientId" not in row for row in demand.json()["signals"])


@pytest.mark.asyncio
async def test_cross_role_route_is_denied(client: AsyncClient) -> None:
    patient = await login(client, "patient")
    response = await client.get(
        "/api/v1/government/metrics",
        headers={"Authorization": f"Bearer {patient['accessToken']}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_caregiver_revocation_blocks_further_access(client: AsyncClient) -> None:
    from sqlalchemy import select

    from carepath.db import SessionLocal
    from carepath.models import CaregiverGrant

    caregiver = await login(client, "caregiver")
    headers = {"Authorization": f"Bearer {caregiver['accessToken']}"}
    dashboard = await client.get("/api/v1/patient/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    task_id = next(
        task["id"]
        for task in dashboard.json()["tasks"]
        if task["status"] != "COMPLETED"
    )

    async with SessionLocal() as db:
        grant = await db.scalar(
            select(CaregiverGrant).where(CaregiverGrant.active.is_(True))
        )
        assert grant is not None
        grant.active = False
        await db.commit()

    blocked_dashboard = await client.get("/api/v1/patient/dashboard", headers=headers)
    assert blocked_dashboard.status_code in {403, 404}
    blocked_task = await client.post(
        f"/api/v1/tasks/{task_id}/complete",
        headers=headers,
        json={},
    )
    assert blocked_task.status_code == 403


@pytest.mark.asyncio
async def test_cross_hospital_plan_read_is_denied(client: AsyncClient) -> None:
    doctor = await login(client, "doctor")
    own = await client.get(
        "/api/v1/treatment-plans/plan-main",
        headers={"Authorization": f"Bearer {doctor['accessToken']}"},
    )
    assert own.status_code == 200, own.text

    other_doctor = await login(client, "doctor_b")
    denied = await client.get(
        "/api/v1/treatment-plans/plan-main",
        headers={"Authorization": f"Bearer {other_doctor['accessToken']}"},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_duplicate_official_dataset_is_rejected(client: AsyncClient) -> None:
    admin = await login(client, "admin")
    headers = {"Authorization": f"Bearer {admin['accessToken']}"}
    response = await client.post(
        "/api/v1/admin/official-datasets",
        headers=headers,
        json={
            "sourceCode": "NMPA",
            "title": "重复校验值测试快照",
            "version": "test",
            "sourceUrl": "https://www.nmpa.gov.cn/",
            "checksum": "demo-nmpa-20261022-a1b2c3d4",
            "reviewer": "测试审核员",
            "content": {},
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_pharma_signals_respect_publish_threshold(client: AsyncClient) -> None:
    pharma = await login(client, "pharma")
    demand = await client.get(
        "/api/v1/pharma/demand",
        headers={"Authorization": f"Bearer {pharma['accessToken']}"},
    )
    assert demand.status_code == 200, demand.text
    signals = demand.json()["signals"]
    assert signals, "seeded data should publish at least one regional signal"
    for signal in signals:
        assert signal["organizationCount"] >= 3
        assert signal["patientMonths"] >= 50
        assert "patientId" not in signal


@pytest.mark.asyncio
async def test_government_suppresses_small_region(client: AsyncClient) -> None:
    from datetime import date

    from carepath.db import SessionLocal
    from carepath.models import Organization, TreatmentPlan

    async with SessionLocal() as db:
        organization = Organization(
            id="org-small-region",
            name="小样本医院",
            type="HOSPITAL",
            region_code="999999",
            verified=False,
        )
        db.add(organization)
        await db.flush()
        db.add(
            TreatmentPlan(
                template_id="template-hypertension",
                patient_id="patient-main",
                doctor_id="user-doctor",
                organization_id=organization.id,
                title="小样本区域计划",
                status="ACTIVE",
                start_date=date.today(),
                content={},
            )
        )
        await db.commit()

    regulator = await login(client, "regulator")
    metrics = await client.get(
        "/api/v1/government/metrics",
        headers={"Authorization": f"Bearer {regulator['accessToken']}"},
    )
    assert metrics.status_code == 200, metrics.text
    rows = {row["regionCode"]: row for row in metrics.json()["regions"]}

    assert rows["999999"]["suppressed"] is True
    assert rows["999999"]["activePlans"] is None
    assert rows["999999"]["openAlerts"] is None
    assert rows["999999"]["taskCompletionRate"] is None
    assert rows["310000"]["suppressed"] is False