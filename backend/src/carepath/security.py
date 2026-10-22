from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
TOKEN_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=32,
    )
    return "$".join(
        [
            "scrypt",
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = encoded.split("$", 5)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _create_token(
    *,
    user_id: str,
    role: str,
    organization_id: str | None,
    secret_key: str,
    expires_delta: timedelta,
    token_type: Literal["access", "refresh"],
    csrf_token: str | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "org": organization_id,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": secrets.token_urlsafe(16),
    }
    if csrf_token:
        payload["csrf"] = csrf_token
    return jwt.encode(payload, secret_key, algorithm=TOKEN_ALGORITHM)


def create_access_token(
    *,
    user_id: str,
    role: str,
    organization_id: str | None,
    secret_key: str,
    expires_delta: timedelta = timedelta(minutes=15),
    csrf_token: str | None = None,
) -> str:
    return _create_token(
        user_id=user_id,
        role=role,
        organization_id=organization_id,
        secret_key=secret_key,
        expires_delta=expires_delta,
        token_type="access",
        csrf_token=csrf_token,
    )


def create_refresh_token(
    *,
    user_id: str,
    role: str,
    organization_id: str | None,
    secret_key: str,
    expires_delta: timedelta = timedelta(days=14),
) -> str:
    return _create_token(
        user_id=user_id,
        role=role,
        organization_id=organization_id,
        secret_key=secret_key,
        expires_delta=expires_delta,
        token_type="refresh",
    )


def decode_token(
    token: str,
    secret_key: str,
) -> dict[str, Any]:
    return jwt.decode(
        token,
        secret_key,
        algorithms=[TOKEN_ALGORITHM],
        options={"verify_exp": True},
        leeway=0,
    )


def verify_token(
    token: str,
    *,
    secret_key: str,
    expected_type: Literal["access", "refresh"],
) -> dict[str, Any]:
    payload = decode_token(token, secret_key)
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload
