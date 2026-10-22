from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from carepath.integrations.contracts import (
    IdempotencyStore,
    IntegrationPort,
    IntegrationRequest,
    IntegrationResult,
    PermanentIntegrationError,
)
from carepath.integrations.retry import RetryPolicy, Sleep, execute_with_retry


@dataclass
class InMemoryIdempotencyStore:
    """Process-local store for tests and single-process demos only."""

    _results: dict[str, IntegrationResult] = field(default_factory=dict)

    async def get(self, key: str) -> IntegrationResult | None:
        return self._results.get(key)

    async def put(self, key: str, result: IntegrationResult) -> None:
        self._results[key] = result


async def execute_idempotent(
    port: IntegrationPort,
    request: IntegrationRequest,
    store: IdempotencyStore,
    *,
    policy: RetryPolicy = RetryPolicy(),
    sleep: Sleep = asyncio.sleep,
) -> IntegrationResult:
    if not request.idempotency_key.strip():
        raise PermanentIntegrationError("写操作必须提供幂等键")
    cached = await store.get(request.idempotency_key)
    if cached is not None:
        return cached
    result = await execute_with_retry(port, request, policy=policy, sleep=sleep)
    await store.put(request.idempotency_key, result)
    return result
