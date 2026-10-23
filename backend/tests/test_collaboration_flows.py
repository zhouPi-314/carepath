from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, username: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_user_login_marks_patient_and_family(client: AsyncClient) -> None:
    patient = await _login(client, "patient", "Pa2026!care")
    family = await _login(client, "caregiver", "Ca2026!care")

    assert patient["user"]["identityLabel"] == "病患"
    assert family["user"]["identityLabel"] == "家属"


@pytest.mark.asyncio
async def test_hospital_staff_patient_tags_transfer_and_records(client: AsyncClient) -> None:
    admin = await _login(client, "hospital", "Ho2026!care")
    headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    staff = await client.get("/api/v1/hospital/staff", headers=headers)
    assert staff.status_code == 200, staff.text
    assert any(item["role"] == "DOCTOR" for item in staff.json())

    tagged = await client.patch(
        "/api/v1/hospital/patients/patient-main/tags",
        headers=headers,
        json={"careLevel": "CHRONIC", "tags": ["高血压", "随访中"]},
    )
    assert tagged.status_code == 200, tagged.text
    assert tagged.json()["careLevel"] == "CHRONIC"

    transfer = await client.post(
        "/api/v1/hospital/transfers",
        headers=headers,
        json={
            "patientId": "patient-main",
            "toOrganizationId": "org-community",
            "level": "COMMUNITY",
            "reason": "稳定期下沉社区",
        },
    )
    assert transfer.status_code == 201, transfer.text

    record = await client.post(
        "/api/v1/hospital/treatment-records",
        headers=headers,
        json={
            "planId": "plan-main",
            "recordType": "PROGRESS",
            "title": "复诊记录",
            "summary": "血压平稳，继续当前方案。",
            "visibility": "CARE_TEAM_AND_FAMILY",
        },
    )
    assert record.status_code == 201, record.text

    doctor = await _login(client, "doctor", "Do2026!care")
    doctor_headers = {"Authorization": f"Bearer {doctor['accessToken']}"}
    records = await client.get(
        "/api/v1/hospital/treatment-records/patient-main",
        headers=doctor_headers,
    )
    assert records.status_code == 200, records.text
    assert any(item["title"] == "复诊记录" for item in records.json())


@pytest.mark.asyncio
async def test_family_reads_progress_and_patient_talks_to_doctor(client: AsyncClient) -> None:
    family = await _login(client, "caregiver", "Ca2026!care")
    family_headers = {"Authorization": f"Bearer {family['accessToken']}"}

    records = await client.get("/api/v1/patient/records", headers=family_headers)
    assert records.status_code == 200, records.text
    assert records.json()

    patient = await _login(client, "patient", "Pa2026!care")
    patient_headers = {"Authorization": f"Bearer {patient['accessToken']}"}
    sent = await client.post(
        "/api/v1/plans/plan-main/messages",
        headers=patient_headers,
        json={"content": "今天晨起血压 136/84，需要调整用药吗？"},
    )
    assert sent.status_code == 201, sent.text

    doctor = await _login(client, "doctor", "Do2026!care")
    doctor_headers = {"Authorization": f"Bearer {doctor['accessToken']}"}
    messages = await client.get("/api/v1/plans/plan-main/messages", headers=doctor_headers)
    assert messages.status_code == 200, messages.text
    assert any("136/84" in item["content"] for item in messages.json())


@pytest.mark.asyncio
async def test_community_manages_volunteers_tasks_and_deliveries(client: AsyncClient) -> None:
    community = await _login(client, "community", "Co2026!care")
    headers = {"Authorization": f"Bearer {community['accessToken']}"}

    dashboard = await client.get("/api/v1/community/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["volunteerCount"] >= 2

    volunteer = await client.post(
        "/api/v1/community/volunteers",
        headers=headers,
        json={"name": "新志愿者", "phoneMasked": "138****0003", "skills": ["陪诊"]},
    )
    assert volunteer.status_code == 201, volunteer.text

    task = await client.post(
        "/api/v1/community/tasks",
        headers=headers,
        json={
            "title": "社区随访电话",
            "category": "VISIT",
            "patientId": "patient-main",
        },
    )
    assert task.status_code == 201, task.text

    delivery = await client.post(
        "/api/v1/community/deliveries",
        headers=headers,
        json={"patientId": "patient-main", "addressRegion": "310000", "note": "送药上门"},
    )
    assert delivery.status_code == 201, delivery.text


@pytest.mark.asyncio
async def test_community_role_cannot_read_hospital_records(client: AsyncClient) -> None:
    community = await _login(client, "community", "Co2026!care")
    response = await client.get(
        "/api/v1/hospital/treatment-records/patient-main",
        headers={"Authorization": f"Bearer {community['accessToken']}"},
    )
    assert response.status_code == 403
