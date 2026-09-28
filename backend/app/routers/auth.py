from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from app.core.config import settings
from app.db.session import SessionDep
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
# Scope the cookie to the auth routes so it isn't sent with every API request
REFRESH_COOKIE_PATH = router.prefix


def _token_response(access_token: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


def _respond_with_tokens(response: Response, tokens: auth_service.TokenPair) -> TokenResponse:
    """Set the refresh token as an HTTP-only cookie and return the access token as JSON."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=tokens.refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
    )
    return _token_response(tokens.access_token)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, response: Response, session: SessionDep) -> TokenResponse:
    try:
        tokens = await auth_service.register_user(session, payload)
    except auth_service.EmailAlreadyRegisteredError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email is already registered") from None
    return _respond_with_tokens(response, tokens)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, session: SessionDep) -> TokenResponse:
    try:
        tokens = await auth_service.login_user(session, payload)
    except auth_service.InvalidCredentialsError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password") from None
    return _respond_with_tokens(response, tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> TokenResponse:
    try:
        access_token = await auth_service.refresh_access_token(session, refresh_token)
    except auth_service.InvalidRefreshTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token") from None
    return _token_response(access_token)
