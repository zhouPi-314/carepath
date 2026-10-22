from datetime import timedelta

import jwt
import pytest

from carepath.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
    verify_token,
)


def test_password_hash_round_trip_rejects_wrong_password() -> None:
    encoded = hash_password("CarePath123!")

    assert encoded != "CarePath123!"
    assert verify_password("CarePath123!", encoded)
    assert not verify_password("wrong", encoded)


def test_access_token_round_trip_and_wrong_type_rejected() -> None:
    token = create_access_token(
        user_id="user-1",
        role="DOCTOR",
        organization_id="hospital-1",
        secret_key="test-secret-key-with-at-least-32-characters",
        expires_delta=timedelta(minutes=5),
    )
    payload = decode_token(token, "test-secret-key-with-at-least-32-characters")

    assert payload["sub"] == "user-1"
    assert payload["role"] == "DOCTOR"
    assert payload["type"] == "access"

    with pytest.raises(jwt.InvalidTokenError):
        verify_token(
            token,
            secret_key="test-secret-key-with-at-least-32-characters",
            expected_type="refresh",
        )


def test_expired_token_is_rejected() -> None:
    token = create_access_token(
        user_id="user-1",
        role="PATIENT",
        organization_id=None,
        secret_key="test-secret-key-with-at-least-32-characters",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(
            token,
            "test-secret-key-with-at-least-32-characters",
        )
