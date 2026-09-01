from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.errors import BusinessError, ErrorCode
from app.core.security.token import hash_refresh_token
from app.models import RefreshToken
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import (
    authenticate_user,
    logout_user,
    refresh_authentication,
    register_user,
)
from app.utils.datetime import utc_now


async def test_register_hashes_password_and_derives_username(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = await register_user(
            session,
            RegisterRequest(phone="13800138000", password="strong-password"),
        )
        await session.commit()
        assert user.username == "13800138000"
        assert user.password_hash != "strong-password"


async def test_register_rejects_duplicate_identity(async_session_factory) -> None:
    async with async_session_factory() as session:
        await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        assert error.value.error_code == ErrorCode.USER_CONFLICT


async def test_login_rejects_wrong_password_without_leaking_details(async_session_factory) -> None:
    async with async_session_factory() as session:
        await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await authenticate_user(session, LoginRequest(identifier="keeper", password="wrong-pass"), None)
        assert error.value.error_code == ErrorCode.AUTHENTICATION_FAILED


async def test_refresh_rotates_token_and_revokes_old_one(async_session_factory) -> None:
    async with async_session_factory() as session:
        await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        await session.commit()
        auth_result = await authenticate_user(
            session, LoginRequest(identifier="keeper", password="strong-password"), "android-app"
        )
        rotated = await refresh_authentication(session, auth_result.refresh_token)
        assert rotated.refresh_token != auth_result.refresh_token
        with pytest.raises(BusinessError) as error:
            await refresh_authentication(session, auth_result.refresh_token)
        assert error.value.error_code == ErrorCode.REFRESH_TOKEN_INVALID


async def test_logout_revokes_selected_refresh_token(async_session_factory) -> None:
    async with async_session_factory() as session:
        await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        await session.commit()
        auth_result = await authenticate_user(
            session, LoginRequest(identifier="keeper", password="strong-password"), "web"
        )
        await logout_user(session, auth_result.refresh_token)
        with pytest.raises(BusinessError) as error:
            await refresh_authentication(session, auth_result.refresh_token)
        assert error.value.error_code == ErrorCode.REFRESH_TOKEN_INVALID


async def test_expired_refresh_token_is_rejected(async_session_factory) -> None:
    async with async_session_factory() as session:
        await register_user(session, RegisterRequest(username="keeper", password="strong-password"))
        await session.commit()
        auth_result = await authenticate_user(
            session, LoginRequest(identifier="keeper", password="strong-password"), "web"
        )
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(auth_result.refresh_token)
            )
        )
        refresh_record = result.scalar_one()
        refresh_record.expires_at = utc_now() - timedelta(seconds=1)
        await session.commit()
        with pytest.raises(BusinessError) as error:
            await refresh_authentication(session, auth_result.refresh_token)
        assert error.value.error_code == ErrorCode.REFRESH_TOKEN_INVALID
