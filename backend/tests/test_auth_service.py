import pytest

from backend.app.core.errors import BusinessError, ErrorCode
from backend.app.schemas.auth import LoginRequest, RegisterRequest
from backend.app.services.auth import authenticate_user, register_user


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
