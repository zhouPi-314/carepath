from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from carepath.integrations.contracts import (
    IntegrationKind,
    IntegrationNotConfiguredError,
    IntegrationPort,
    IntegrationRequest,
    IntegrationResult,
)
from carepath.integrations.retry import RetryPolicy

_LABELS: dict[IntegrationKind, str] = {
    IntegrationKind.HOSPITAL_HIS: "医院 HIS",
    IntegrationKind.MEDICAL_INSURANCE: "医保",
    IntegrationKind.GOVERNMENT: "政务",
    IntegrationKind.SUPPLY_CHAIN: "供应链",
}


@dataclass(frozen=True)
class IntegrationDescriptor:
    kind: IntegrationKind
    label: str
    configured: bool
    capabilities: tuple[str, ...]
    retry_max_attempts: int
    timeout_seconds: float
    idempotency_required: bool = True


class UnconfiguredIntegration:
    """A reserved port with no partner: every call fails explicitly."""

    def __init__(self, kind: IntegrationKind, label: str, *, timeout_seconds: float = 5.0) -> None:
        self.kind = kind
        self.label = label
        self.configured = False
        self.timeout_seconds = timeout_seconds

    def capabilities(self) -> tuple[str, ...]:
        return ()

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        raise IntegrationNotConfiguredError(
            f"{self.label}端口未配置：需要合作授权与接口文档，平台不伪造联调结果"
        )


class IntegrationRegistry:
    def __init__(
        self,
        ports: Mapping[IntegrationKind, IntegrationPort],
        *,
        policy: RetryPolicy | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._ports = dict(ports)
        self._policy = policy or RetryPolicy()
        self._timeout_seconds = timeout_seconds

    def get(self, kind: IntegrationKind) -> IntegrationPort:
        return self._ports[kind]

    def describe(self) -> list[IntegrationDescriptor]:
        return [
            IntegrationDescriptor(
                kind=port.kind,
                label=_LABELS.get(port.kind, port.kind.value),
                configured=port.configured,
                capabilities=port.capabilities(),
                retry_max_attempts=self._policy.max_attempts,
                timeout_seconds=self._timeout_seconds,
            )
            for port in self._ports.values()
        ]


def build_default_registry(
    *,
    policy: RetryPolicy | None = None,
    timeout_seconds: float = 5.0,
) -> IntegrationRegistry:
    ports = {
        kind: UnconfiguredIntegration(kind, _LABELS[kind], timeout_seconds=timeout_seconds)
        for kind in IntegrationKind
    }
    return IntegrationRegistry(ports, policy=policy, timeout_seconds=timeout_seconds)
