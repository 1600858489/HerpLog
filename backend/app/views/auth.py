from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.response import ResponseEnvelope, success_response
from backend.app.core.security.dependencies import get_current_user
from backend.app.infra.database import get_db_session
from backend.app.models import User
from backend.app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)
from backend.app.services import authenticate_user, logout_user, refresh_authentication, register_user


auth_router = APIRouter()


@auth_router.post(
    "/register",
    response_model=ResponseEnvelope[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseEnvelope[UserResponse]:
    """Register an account and return its public profile."""
    user = await register_user(session, request)
    return success_response(UserResponse.model_validate(user))


@auth_router.post("/login", response_model=ResponseEnvelope[AuthResponse])
async def login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseEnvelope[AuthResponse]:
    """Authenticate an account and issue access and refresh credentials."""
    result = await authenticate_user(session, request, request.device_info)
    return success_response(
        AuthResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
            expires_in=result.expires_in,
            user=UserResponse.model_validate(result.user),
        )
    )


@auth_router.post("/refresh", response_model=ResponseEnvelope[AuthResponse])
async def refresh(
    request: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseEnvelope[AuthResponse]:
    """Rotate a refresh token and issue a new access token."""
    result = await refresh_authentication(session, request.refresh_token)
    return success_response(
        AuthResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
            expires_in=result.expires_in,
            user=UserResponse.model_validate(result.user),
        )
    )


@auth_router.post("/logout", response_model=ResponseEnvelope[None])
async def logout(
    request: LogoutRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResponseEnvelope[None]:
    """Revoke one refresh-token session."""
    await logout_user(session, request.refresh_token)
    return success_response(None)


@auth_router.get("/me", response_model=ResponseEnvelope[UserResponse])
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseEnvelope[UserResponse]:
    """Return the authenticated user's public profile."""
    return success_response(UserResponse.model_validate(current_user))


__all__ = ["auth_router"]
