from __future__ import annotations

import pytest

from carepath.integrations import (
    InMemoryIdempotencyStore,
    IntegrationKind,
    IntegrationNotConfiguredError,
    IntegrationRequest,
    IntegrationResult,
    IntegrationTimeoutError,
    PermanentIntegrationError,
    RetryPolicy,
    TransientIntegrationError,
    build_default_registry,
    execute_idempotent,
    execute_with_retry,
)


async def _no_sleep(_: float) -> None:
    return None


class FakePort:
    kind = IntegrationKind.HOSPITAL_HIS
    configured = True

    def __init__(self, failures: list[Exception]) -> None:
        self.failures = failures
        self.calls = 0

    def capabilities(self) -> tuple[str, ...]:
        return ("patient.read",)

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        self.calls += 1
        if self.failures:
            raise self.failures.pop(0)
        return IntegrationResult(ok=True, data={"echo": request.operation})


def _request(key: str = "idem-1") -> IntegrationRequest:
    return IntegrationRequest(operation="sync", idempotency_key=key, timeout_seconds=1.0)


@pytest.mark.asyncio
async def test_transient_error_is_retried_then_succeeds() -> None:
    port = FakePort([TransientIntegrationError("503")])

    result = await execute_with_retry(port, _request(), sleep=_no_sleep)

    assert result.ok is True
    assert result.retries == 1
    assert port.calls == 2


@pytest.mark.asyncio
async def test_permanent_error_is_not_retried() -> None:
    port = FakePort([PermanentIntegrationError("invalid payload")])

    with pytest.raises(PermanentIntegrationError):
        await execute_with_retry(port, _request(), sleep=_no_sleep)
    assert port.calls == 1


@pytest.mark.asyncio
async def test_timeout_exhausts_retries_and_raises_transient_error() -> None:
    port = FakePort([TimeoutError(), TimeoutError(), TimeoutError()])

    with pytest.raises(IntegrationTimeoutError):
        await execute_with_retry(port, _request(), sleep=_no_sleep)
    assert port.calls == 3


@pytest.mark.asyncio
async def test_missing_idempotency_key_is_rejected_before_any_call() -> None:
    port = FakePort([])

    with pytest.raises(PermanentIntegrationError):
        await execute_with_retry(port, _request(key="   "), sleep=_no_sleep)
    assert port.calls == 0


@pytest.mark.asyncio
async def test_idempotent_execution_returns_cached_result() -> None:
    port = FakePort([])
    store = InMemoryIdempotencyStore()

    first = await execute_idempotent(port, _request(), store, sleep=_no_sleep)
    second = await execute_idempotent(port, _request(), store, sleep=_no_sleep)

    assert first == second
    assert port.calls == 1


@pytest.mark.asyncio
async def test_unconfigured_port_never_pretends_success() -> None:
    registry = build_default_registry()
    port = registry.get(IntegrationKind.MEDICAL_INSURANCE)

    with pytest.raises(IntegrationNotConfiguredError):
        await port.execute(_request())


def test_default_registry_describes_all_reserved_ports() -> None:
    descriptors = build_default_registry().describe()

    assert {item.kind for item in descriptors} == set(IntegrationKind)
    assert all(item.configured is False for item in descriptors)
    assert all(item.retry_max_attempts == 3 for item in descriptors)
    assert all(item.idempotency_required for item in descriptors)


def test_retry_policy_backs_off_with_a_cap() -> None:
    policy = RetryPolicy(max_attempts=4, base_delay_seconds=0.5, max_delay_seconds=1.5)

    assert policy.delay(1) == 0.5
    assert policy.delay(2) == 1.0
    assert policy.delay(3) == 1.5
    assert policy.delay(10) == 1.5


@pytest.mark.asyncio
async def test_admin_sees_reserved_ports_and_patient_is_denied(client) -> None:
    admin = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "CarePath123!"},
    )
    assert admin.status_code == 200
    headers = {"Authorization": f"Bearer {admin.json()['accessToken']}"}

    response = await client.get("/api/v1/admin/integrations", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["integrations"]) == 4
    assert all(item["configured"] is False for item in body["integrations"])
    assert "不伪造" in body["disclaimer"]

    patient = await client.post(
        "/api/v1/auth/login",
        json={"username": "patient", "password": "CarePath123!"},
    )
    denied = await client.get(
        "/api/v1/admin/integrations",
        headers={"Authorization": f"Bearer {patient.json()['accessToken']}"},
    )
    assert denied.status_code == 403
