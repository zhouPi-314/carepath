from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace

from carepath.integrations.contracts import (
    IntegrationPort,
    IntegrationRequest,
    IntegrationResult,
    IntegrationTimeoutError,
    PermanentIntegrationError,
    TransientIntegrationError,
)

Sleep = Callable[[float], Awaitable[None]]


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.2
    max_delay_seconds: float = 2.0

    def delay(self, attempt: int) -> float:
        return min(self.base_delay_seconds * (2 ** (attempt - 1)), self.max_delay_seconds)


async def execute_with_retry(
    port: IntegrationPort,
    request: IntegrationRequest,
    *,
    policy: RetryPolicy = RetryPolicy(),
    sleep: Sleep = asyncio.sleep,
) -> IntegrationResult:
    if not request.idempotency_key.strip():
        raise PermanentIntegrationError("写操作必须提供幂等键")
    if request.timeout_seconds <= 0:
        raise PermanentIntegrationError("超时时间必须大于 0")

    last_error: TransientIntegrationError | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            result = await asyncio.wait_for(
                port.execute(request),
                timeout=request.timeout_seconds,
            )
            return replace(result, retries=attempt - 1)
        except TimeoutError as exc:
            last_error = IntegrationTimeoutError(
                f"{port.kind.value} 调用超时（{request.timeout_seconds}s）"
            )
            last_error.__cause__ = exc
        except PermanentIntegrationError:
            raise
        except TransientIntegrationError as exc:
            last_error = exc
        if attempt < policy.max_attempts:
            await sleep(policy.delay(attempt))

    if last_error is None:  # pragma: no cover - defensive
        raise TransientIntegrationError("外部系统调用失败")
    raise last_error
