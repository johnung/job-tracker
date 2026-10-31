from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_hash = PasswordHash.recommended()

# Verify against this when the email doesn't match a user, so a login for an
# unknown email takes as long as a wrong password and doesn't reveal which
# emails exist.
DUMMY_PASSWORD_HASH = password_hash.hash("dummy-password")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": datetime.now(UTC) + expires_delta}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> int:
    """Return the user id from a token.

    Raises jwt.InvalidTokenError if the token is malformed, tampered with,
    expired, or missing claims.
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub"]},
    )
    try:
        return int(payload["sub"])
    except ValueError as exc:
        raise jwt.InvalidTokenError("sub is not a user id") from exc
