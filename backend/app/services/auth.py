from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.core.errors import BusinessError, ErrorCode
from backend.app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from backend.app.models import RefreshToken, User
from backend.app.selectors import get_refresh_token_by_hash, get_user_by_identifier
from backend.app.utils.datetime import utc_now

if TYPE_CHECKING:
    from backend.app.schemas.auth import LoginRequest, RegisterRequest


@dataclass(frozen=True)
class AuthResult:
    """Carry newly issued credentials and the authenticated user to the View."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: User


def _build_auth_result(user: User, refresh_token: str) -> AuthResult:
    """Build access-token response data for an authenticated user."""
    settings = get_settings()
    return AuthResult(
        access_token=create_access_token(str(user.uuid)),
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user,
    )


async def register_user(session: AsyncSession, request: "RegisterRequest") -> User:
    """Register an account after checking normalized identity conflicts."""
    for identifier in (request.username, request.phone, request.email):
        if identifier is not None and await get_user_by_identifier(session, str(identifier)):
            raise BusinessError(ErrorCode.USER_CONFLICT)

    user = User(
        username=request.username,
        phone=request.phone,
        email=str(request.email) if request.email is not None else None,
        password_hash=hash_password(request.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession, request: "LoginRequest", device_info: str | None
) -> AuthResult:
    """Authenticate an account and persist one refresh-token session."""
    user = await get_user_by_identifier(session, request.identifier)
    if user is None or not verify_password(request.password, user.password_hash):
        raise BusinessError(ErrorCode.AUTHENTICATION_FAILED)

    settings = get_settings()
    refresh_token = generate_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=utc_now() + timedelta(days=settings.refresh_token_expire_days),
            device_info=device_info,
        )
    )
    await session.commit()
    return _build_auth_result(user, refresh_token)


async def refresh_authentication(session: AsyncSession, refresh_token: str) -> AuthResult:
    """Rotate a valid refresh token and revoke the presented credential."""
    token_record = await get_refresh_token_by_hash(session, hash_refresh_token(refresh_token))
    if (
        token_record is None
        or token_record.revoked_at is not None
        or token_record.expires_at <= utc_now()
        or token_record.user.deleted_at is not None
    ):
        raise BusinessError(ErrorCode.REFRESH_TOKEN_INVALID)

    token_record.revoked_at = utc_now()
    new_refresh_token = generate_refresh_token()
    session.add(
        RefreshToken(
            user_id=token_record.user_id,
            token_hash=hash_refresh_token(new_refresh_token),
            expires_at=utc_now() + timedelta(days=get_settings().refresh_token_expire_days),
            device_info=token_record.device_info,
        )
    )
    await session.commit()
    return _build_auth_result(token_record.user, new_refresh_token)


async def logout_user(session: AsyncSession, refresh_token: str) -> None:
    """Revoke one active refresh-token session."""
    token_record = await get_refresh_token_by_hash(session, hash_refresh_token(refresh_token))
    if token_record is None or token_record.revoked_at is not None:
        raise BusinessError(ErrorCode.REFRESH_TOKEN_INVALID)
    token_record.revoked_at = utc_now()
    await session.commit()


__all__ = [
    "AuthResult",
    "authenticate_user",
    "logout_user",
    "refresh_authentication",
    "register_user",
]
