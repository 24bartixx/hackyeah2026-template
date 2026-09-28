from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_token,
    decode_token,
    generate_salt,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthError(Exception):
    """Base class for auth failures; routers translate these into HTTP responses."""


class EmailAlreadyRegisteredError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str


def _issue_tokens(user_id: int) -> TokenPair:
    return TokenPair(
        access_token=create_token(user_id, "access"),
        refresh_token=create_token(user_id, "refresh"),
    )


async def register_user(session: AsyncSession, payload: RegisterRequest) -> TokenPair:
    if await session.scalar(select(User.user_id).where(User.email == payload.email)) is not None:
        raise EmailAlreadyRegisteredError

    salt = generate_salt()
    # Argon2 is deliberately CPU/memory heavy; keep it off the event loop
    password_hash = await run_in_threadpool(hash_password, payload.password, salt)
    user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password_hash=password_hash,
        salt=salt,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        # Lost a race with a concurrent registration of the same email
        await session.rollback()
        raise EmailAlreadyRegisteredError from None

    return _issue_tokens(user.user_id)


async def login_user(session: AsyncSession, payload: LoginRequest) -> TokenPair:
    user = await session.scalar(select(User).where(User.email == payload.email))
    # Verify against a dummy hash for unknown emails so timing doesn't reveal registered accounts
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_ok = await run_in_threadpool(verify_password, payload.password, password_hash)
    if user is None or not password_ok:
        raise InvalidCredentialsError

    return _issue_tokens(user.user_id)


async def refresh_access_token(session: AsyncSession, refresh_token: str | None) -> str:
    user_id = decode_token(refresh_token, "refresh") if refresh_token else None
    if user_id is None or await session.get(User, user_id) is None:
        raise InvalidRefreshTokenError

    return create_token(user_id, "access")
