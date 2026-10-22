from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class IntegrationKind(StrEnum):
    HOSPITAL_HIS = "HIS"
    MEDICAL_INSURANCE = "MEDICAL_INSURANCE"
    GOVERNMENT = "GOVERNMENT"
    SUPPLY_CHAIN = "SUPPLY_CHAIN"


class IntegrationError(Exception):
    """Base class for external-system failures."""


class IntegrationNotConfiguredError(IntegrationError):
    """Raised when no partnership or adapter exists; never retried."""


class TransientIntegrationError(IntegrationError):
    """Retryable failure: timeout, 5xx, connection reset."""


class IntegrationTimeoutError(TransientIntegrationError):
    """The remote call exceeded the configured timeout."""


class PermanentIntegrationError(IntegrationError):
    """Non-retryable failure: invalid request or rejected payload."""


@dataclass(frozen=True)
class IntegrationRequest:
    operation: str
    idempotency_key: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 5.0


@dataclass(frozen=True)
class IntegrationResult:
    ok: bool
    data: Mapping[str, Any] = field(default_factory=dict)
    external_id: str | None = None
    retries: int = 0


class IntegrationPort(Protocol):
    kind: IntegrationKind
    configured: bool

    def capabilities(self) -> tuple[str, ...]: ...

    async def execute(self, request: IntegrationRequest) -> IntegrationResult: ...


class HospitalInformationSystemPort(IntegrationPort, Protocol):
    """Patient/encounter/order exchange with a hospital HIS."""


class MedicalInsurancePort(IntegrationPort, Protocol):
    """Coverage and settlement status exchange with medical insurance."""


class GovernmentDataPort(IntegrationPort, Protocol):
    """Regulatory reporting and public-data exchange."""


class SupplyChainPort(IntegrationPort, Protocol):
    """Drug supply and capacity exchange with manufacturers."""


class IdempotencyStore(Protocol):
    async def get(self, key: str) -> IntegrationResult | None: ...

    async def put(self, key: str, result: IntegrationResult) -> None: ...
