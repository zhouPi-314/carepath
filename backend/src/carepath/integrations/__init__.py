"""Reserved ports for external systems (HIS, insurance, government, supply chain).

No adapter here performs a real integration. The default registry contains
explicitly unconfigured ports so a missing partnership can never look like a
successful call.
"""

from carepath.integrations.adapters import (
    IntegrationDescriptor,
    IntegrationRegistry,
    UnconfiguredIntegration,
    build_default_registry,
)
from carepath.integrations.contracts import (
    HospitalInformationSystemPort,
    IdempotencyStore,
    IntegrationError,
    IntegrationKind,
    IntegrationNotConfiguredError,
    IntegrationPort,
    IntegrationRequest,
    IntegrationResult,
    IntegrationTimeoutError,
    MedicalInsurancePort,
    PermanentIntegrationError,
    TransientIntegrationError,
)
from carepath.integrations.idempotency import InMemoryIdempotencyStore, execute_idempotent
from carepath.integrations.retry import RetryPolicy, execute_with_retry

__all__ = [
    "HospitalInformationSystemPort",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "IntegrationDescriptor",
    "IntegrationError",
    "IntegrationKind",
    "IntegrationNotConfiguredError",
    "IntegrationPort",
    "IntegrationRegistry",
    "IntegrationRequest",
    "IntegrationResult",
    "IntegrationTimeoutError",
    "MedicalInsurancePort",
    "PermanentIntegrationError",
    "RetryPolicy",
    "TransientIntegrationError",
    "UnconfiguredIntegration",
    "build_default_registry",
    "execute_idempotent",
    "execute_with_retry",
]
