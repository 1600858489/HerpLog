from uuid import UUID

from fastapi.security import HTTPAuthorizationCredentials

from app.core.errors import BusinessError, ErrorCode
from app.core.security.dependencies import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import authenticate_user, register_user


async def test_current_user_dependency_returns_user(async_session_factory) -> None:
    async with async_session_factory() as session:
        user = await register_user(
            session,
            RegisterRequest(username="keeper", password="strong-password"),
        )
        await session.commit()
        auth_result = await authenticate_user(
            session,
            LoginRequest(identifier="keeper", password="strong-password"),
            "test",
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=auth_result.access_token
        )
        current_user = await get_current_user(credentials, session)
        assert isinstance(current_user, User)
        assert current_user.uuid == user.uuid


async def test_current_user_dependency_requires_credentials(async_session_factory) -> None:
    async with async_session_factory() as session:
        try:
            await get_current_user(None, session)
        except BusinessError as error:
            assert error.error_code == ErrorCode.UNAUTHORIZED
        else:
            raise AssertionError("missing credentials must raise BusinessError")
