from __future__ import annotations

import pytest
from httpx import AsyncClient

from carepath.logging_utils import mask_id_card, mask_phone, redact_mapping


def test_redact_mapping_masks_credentials_and_nested_identifiers() -> None:
    payload = {
        "username": "patient",
        "password": "CarePath123!",
        "accessToken": "abc",
        "profile": {"phone": "13812345678", "recordNumber": "DEMO-1"},
        "items": [{"authorization": "Bearer x"}],
        "note": "正常字段",
    }

    redacted = redact_mapping(payload)

    assert redacted["password"] == "***"
    assert redacted["accessToken"] == "***"
    assert redacted["profile"]["phone"] == "***"
    assert redacted["profile"]["recordNumber"] == "***"
    assert redacted["items"][0]["authorization"] == "***"
    assert redacted["username"] == "patient"
    assert redacted["note"] == "正常字段"


def test_mask_helpers_keep_edges() -> None:
    assert mask_phone("13812345678") == "138****5678"
    assert mask_phone("123") == "***"
    assert mask_id_card("310101199001011234") == "3101" + "*" * 10 + "1234"


@pytest.mark.asyncio
async def test_health_reports_release_version(client: AsyncClient) -> None:
    from carepath import __version__

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["version"] == __version__


@pytest.mark.asyncio
async def test_invalid_request_has_unified_error_without_echoing_input(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "patient", "password": "short"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"
    assert body["message"]
    assert body["requestId"]
    assert response.headers["X-Request-ID"] == body["requestId"]
    assert all("input" not in detail for detail in body["details"])
    assert '"short"' not in response.text


@pytest.mark.asyncio
async def test_task_completion_replay_is_idempotent(client: AsyncClient) -> None:
    from sqlalchemy import func, select

    from carepath.db import SessionLocal
    from carepath.models import AuditEvent, OutboxEvent

    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "caregiver", "password": "Ca2026!care"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}

    dashboard = await client.get("/api/v1/patient/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    task_id = next(
        task["id"]
        for task in dashboard.json()["tasks"]
        if task["status"] != "COMPLETED"
    )

    first = await client.post(
        f"/api/v1/tasks/{task_id}/complete",
        headers=headers,
        json={"note": "首次提交"},
    )
    replay = await client.post(
        f"/api/v1/tasks/{task_id}/complete",
        headers=headers,
        json={"note": "断网后重试"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.json()["status"] == "COMPLETED"
    assert replay.json()["status"] == "COMPLETED"

    async with SessionLocal() as db:
        audit_count = await db.scalar(
            select(func.count(AuditEvent.id)).where(
                AuditEvent.action == "TASK_COMPLETE",
                AuditEvent.resource_id == task_id,
            )
        )
        outbox_count = await db.scalar(
            select(func.count(OutboxEvent.id)).where(
                OutboxEvent.event_type == "TASK_COMPLETED",
                OutboxEvent.patient_id == "patient-main",
            )
        )

    assert audit_count == 1
    assert outbox_count == 1
