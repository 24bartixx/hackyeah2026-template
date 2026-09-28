import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import hash_secret

from app.core.config import settings

TokenType = Literal["access", "refresh"]

# argon2-cffi defaults follow the RFC 9106 low-memory Argon2id profile
_hasher = PasswordHasher()
SALT_BYTES = 16


def generate_salt() -> str:
    return secrets.token_hex(SALT_BYTES)


def hash_password(password: str, salt: str) -> str:
    """Argon2id-hash `password` with an explicit hex `salt`; returns the PHC-encoded hash."""
    return hash_secret(
        password.encode(),
        bytes.fromhex(salt),
        time_cost=_hasher.time_cost,
        memory_cost=_hasher.memory_cost,
        parallelism=_hasher.parallelism,
        hash_len=_hasher.hash_len,
        type=_hasher.type,
    ).decode()


def verify_password(password: str, password_hash: str) -> bool:
    # The encoded hash carries its own salt and parameters
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# Verified against when the user does not exist, so login timing doesn't reveal registered emails
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16), generate_salt())


def create_token(user_id: int, token_type: TokenType) -> str:
    now = datetime.now(UTC)
    ttl = (
        timedelta(minutes=settings.access_token_expire_minutes)
        if token_type == "access"
        else timedelta(days=settings.refresh_token_expire_days)
    )
    payload = {"sub": str(user_id), "type": token_type, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: TokenType) -> int | None:
    """Return the user id if `token` is a valid, unexpired token of `expected_type`, else None."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except jwt.InvalidTokenError:
        return None
    if payload.get("type") != expected_type:
        return None
    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        return None
