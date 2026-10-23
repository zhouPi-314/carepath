"""Redaction helpers so credentials and patient identifiers never reach logs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

MASK = "***"

SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "secretkey",
        "token",
        "accesstoken",
        "refreshtoken",
        "authorization",
        "cookie",
        "setcookie",
        "csrf",
        "idcard",
        "idnumber",
        "recordnumber",
        "phone",
        "mobile",
        "diagnosis",
        "clinicalnote",
    }
)


def _normalise(key: object) -> str:
    return str(key).replace("_", "").replace("-", "").lower()


def redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy with sensitive keys masked, recursively."""
    result: dict[str, Any] = {}
    for key, item in value.items():
        if _normalise(key) in SENSITIVE_KEYS:
            result[str(key)] = MASK
        elif isinstance(item, Mapping):
            result[str(key)] = redact_mapping(item)
        elif isinstance(item, (list, tuple)):
            result[str(key)] = [
                redact_mapping(entry) if isinstance(entry, Mapping) else entry
                for entry in item
            ]
        else:
            result[str(key)] = item
    return result


def mask_phone(value: str) -> str:
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) < 7:
        return MASK
    return f"{digits[:3]}****{digits[-4:]}"


def mask_id_card(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) < 8:
        return MASK
    return cleaned[:4] + "*" * (len(cleaned) - 8) + cleaned[-4:]
