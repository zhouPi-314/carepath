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
async def test_transfer_can_be_accepted_by_receiving_community(client: AsyncClient) -> None:
    hospital = await _login(client, "hospital", "Ho2026!care")
    created = await client.post(
        "/api/v1/hospital/transfers",
        headers={"Authorization": f"Bearer {hospital['accessToken']}"},
        json={
            "patientId": "patient-main",
            "toOrganizationId": "org-community",
            "level": "COMMUNITY",
            "reason": "稳定期社区随访",
        },
    )
    assert created.status_code == 201, created.text
    transfer_id = created.json()["id"]

    community = await _login(client, "community", "Co2026!care")
    headers = {"Authorization": f"Bearer {community['accessToken']}"}
    incoming = await client.get("/api/v1/community/transfers", headers=headers)
    assert incoming.status_code == 200
    assert any(item["id"] == transfer_id for item in incoming.json())

    accepted = await client.post(
        f"/api/v1/community/transfers/{transfer_id}/status",
        headers=headers,
        json={"status": "ACCEPTED", "note": "社区已接收"},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_messages_can_be_marked_read(client: AsyncClient) -> None:
    patient = await _login(client, "patient", "Pa2026!care")
    sent = await client.post(
        "/api/v1/plans/plan-main/messages",
        headers={"Authorization": f"Bearer {patient['accessToken']}"},
        json={"content": "最近睡眠一般，是否需要调整随访？"},
    )
    assert sent.status_code == 201

    doctor = await _login(client, "doctor", "Do2026!care")
    headers = {"Authorization": f"Bearer {doctor['accessToken']}"}
    marked = await client.post("/api/v1/plans/plan-main/messages/read", headers=headers)
    assert marked.status_code == 200
    assert marked.json()["updated"] >= 1

    messages = await client.get("/api/v1/plans/plan-main/messages", headers=headers)
    assert any(item["readAt"] for item in messages.json())


@pytest.mark.asyncio
async def test_delivery_is_linked_to_pharma_and_can_be_confirmed(client: AsyncClient) -> None:
    community = await _login(client, "community", "Co2026!care")
    community_headers = {"Authorization": f"Bearer {community['accessToken']}"}
    created = await client.post(
        "/api/v1/community/deliveries",
        headers=community_headers,
        json={
            "patientId": "patient-main",
            "productId": "product-demo-1",
            "addressRegion": "310000",
            "note": "社区代领并配送",
        },
    )
    assert created.status_code == 201, created.text
    delivery_id = created.json()["id"]

    pharma = await _login(client, "pharma", "Ph2026!care")
    pharma_headers = {"Authorization": f"Bearer {pharma['accessToken']}"}
    deliveries = await client.get("/api/v1/pharma/deliveries", headers=pharma_headers)
    assert deliveries.status_code == 200, deliveries.text
    assert any(item["id"] == delivery_id for item in deliveries.json())

    confirmed = await client.post(
        f"/api/v1/pharma/deliveries/{delivery_id}/confirm",
        headers=pharma_headers,
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_mobile_summary_is_role_aware(client: AsyncClient) -> None:
    community = await _login(client, "community", "Co2026!care")
    summary = await client.get(
        "/api/v1/mobile/summary",
        headers={"Authorization": f"Bearer {community['accessToken']}"},
    )
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["role"] == "COMMUNITY_ORG"
    assert body["identityLabel"] == "社区与志愿组织"
    assert body["heading"]

    hospital = await _login(client, "hospital", "Ho2026!care")
    hospital_summary = await client.get(
        "/api/v1/mobile/summary",
        headers={"Authorization": f"Bearer {hospital['accessToken']}"},
    )
    assert hospital_summary.status_code == 200
    assert hospital_summary.json()["role"] == "HOSPITAL_ADMIN"


@pytest.mark.asyncio
async def test_volunteer_has_role_summary_and_tasks(client: AsyncClient) -> None:
    volunteer = await _login(client, "volunteer", "Vo2026!care")
    headers = {"Authorization": f"Bearer {volunteer['accessToken']}"}

    summary = await client.get("/api/v1/mobile/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["role"] == "VOLUNTEER"
    assert body["identityLabel"] == "志愿者"
    assert body["items"]

    tasks = await client.get("/api/v1/community/my-tasks", headers=headers)
    assert tasks.status_code == 200, tasks.text
    assert tasks.json()
