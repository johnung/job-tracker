from datetime import timedelta

import jwt
import pytest

from app.config import settings
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_does_not_store_plaintext():
    hashed = hash_password("hunter2")
    assert hashed != "hunter2"
    assert hashed.startswith("$argon2")


def test_verify_password_accepts_correct_password():
    assert verify_password("hunter2", hash_password("hunter2"))


def test_verify_password_rejects_wrong_password():
    assert not verify_password("wrong", hash_password("hunter2"))


def test_access_token_round_trips_user_id():
    token = create_access_token(42)
    assert decode_access_token(token) == 42


def test_expired_token_is_rejected():
    token = create_access_token(42, expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_token_signed_with_another_key_is_rejected():
    token = jwt.encode(
        {"sub": "42", "exp": 9999999999}, "some-other-key-that-is-at-least-32-bytes"
    )
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token)


def test_token_without_sub_is_rejected():
    token = jwt.encode(
        {"exp": 9999999999}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)


def test_garbage_token_is_rejected():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-jwt")
